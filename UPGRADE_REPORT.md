# Upgrade report: python_product_recommendations

Branch: `upgrade/modernize-stack` (not committed yet)

## 1. Dependency review

| Item | Before | After | Notes |
|---|---|---|---|
| Python | not specified | 3.12+ (`.python-version`) | Tests pass on 3.12.8 and 3.13.2 |
| Flask | not pinned (no requirements file) | `>=3.1.3,<4` | |
| cloudinary SDK | not pinned | `>=1.46.3,<2` | |
| python-dotenv | not pinned, not listed in the README | `>=1.2.0,<2` | Was imported but missing from the install instructions |
| urllib3 / certifi | implicit | listed explicitly | Used for TLS-verified HTTP |
| FastAPI / Pandas | not used | not added | Out of scope for this app |

Results with the new pins:
- `pip-audit -r requirements.txt` found no known vulnerabilities.
- `pip check` found no broken requirements.
- `python -W error::DeprecationWarning -c "import demo"` raised no deprecation warnings.

### Bugs, deprecated usage and security issues found and fixed

| # | Severity | Issue | Fix |
|---|---|---|---|
| 1 | **Security** | `ssl._create_unverified_context()` turned off TLS certificate checks on the Cloudinary request, which allows man-in-the-middle attacks | The request now uses urllib3 with `CERT_REQUIRED` and the certifi CA bundle |
| 2 | **Bug** | `uploader.upload(..., tag="my_products")`: `tag` isn't an upload parameter, so the SDK ignored it silently. New uploads never got `my_products` and never showed up in the app | Changed to `tags=["my_products"]` |
| 3 | **Bug / rate limit** | `/output` called the Admin API `resource()` once per asset, per top tag, per selected item. That is O(tags × assets × selected) calls on each submission, and the Admin API is rate-limited | One paginated `resources_by_tag(tags=True)` call, cached with a TTL |
| 4 | **Bug** | The "skip selected items" check ran inside the selection loop, so a selected product could be recommended back to the user | `recommender.recommend()` now excludes the whole selection |
| 5 | **Bug** | The cloud name `demo` was hard-coded in the list and delivery URLs, while the Admin API used the user's own cloud. The lookups failed for anyone not on `demo` | The cloud name now comes from `CLOUDINARY_URL`, with `demo` as the fallback |
| 6 | Robustness | A failed Cloudinary call caused an HTTP 500 | The page shows an error message instead |
| 7 | Robustness | Files such as `.DS_Store` in `Images/` were uploaded | Only image extensions are uploaded |
| 8 | Docs | The README pointed to a non-existent `app.py`, the wrong add-on (AI Moderation) and Glitch, which no longer hosts projects | README rewritten |

## 2. Target stack

- **Runtime:** Python 3.12+ (also compatible with 3.13)
- **Web:** Flask 3.1 / Werkzeug 3.1 / Jinja2 3.1
- **Cloudinary:** Python SDK 1.46, Amazon Rekognition Auto Tagging add-on
- **Front end:** server-rendered Jinja templates with the Tailwind CDN (unchanged)
- **Tooling:** pytest, pip-audit (`requirements-dev.txt`)

## 3. Refactor summary

- **Data pipeline** (`catalog.py`): loads the catalog with the Admin API when credentials are set and falls back to the public resource list when they aren't. It normalizes each asset to `{public_id, version, width, height, tags}` and keeps a thread-safe TTL cache that is cleared after uploads.
- **Recommendation model** (`recommender.py`): a pure-Python model with no dependencies. It cleans the tags, builds a profile from the top 3 tags of the selection, and ranks products by overlap score. It returns the same set of products as the original algorithm, now ordered by relevance and without selected items.
- **Image grid**: a responsive CSS grid with `srcset` (1x/2x), `loading="lazy"` below the first row, `fetchpriority="high"` above it, explicit `width`/`height` to prevent layout shift, a placeholder background, `preconnect` to `res.cloudinary.com`, `alt` text and a viewport meta tag.
- **Delivery URLs** are built with `CloudinaryImage.build_url` and match the original URLs exactly (`f_auto/q_auto/c_fill_pad,g_auto,w_100,h_100/v<ver>/<id>`), so images Cloudinary has already generated are reused. A test checks this.
- **Upload** moved from commented-out code to a CLI command: `flask --app demo upload-images`.
- **Unchanged:** the `/` and `/output` routes, the form field names, the checkbox and label markup and CSS, the page copy, `python demo.py`, and the upload options.

## 4. Proposed GitHub repository metadata

Not applied yet: changing the About field affects the public repo, so it waits for your approval.

**About description:**
> Flask product recommendation app that ranks similar e-commerce products using Cloudinary AI auto-tagging (Amazon Rekognition), with f_auto/q_auto optimized, responsive image grids.

**Topics:**
`cloudinary`, `python`, `flask`, `product-recommendations`, `recommendation-system`, `ecommerce`, `auto-tagging`, `aws-rekognition`, `ai-tagging`, `image-optimization`, `f-auto`, `q-auto`, `admin-api`, `responsive-images`

**Command to apply it:**
```sh
gh repo edit cloudinary-devs/python_product_recommendations \
  --description "Flask product recommendation app that ranks similar e-commerce products using Cloudinary AI auto-tagging (Amazon Rekognition), with f_auto/q_auto optimized, responsive image grids." \
  --add-topic cloudinary,python,flask,product-recommendations,recommendation-system,ecommerce,auto-tagging,aws-rekognition,ai-tagging,image-optimization,f-auto,q-auto,admin-api,responsive-images
```

## 5. Verification checklist

| Check | Result | How |
|---|---|---|
| Dependencies install on Python 3.12 | ✅ | `pip install -r requirements.txt` |
| No known vulnerabilities | ✅ | `pip-audit -r requirements.txt` |
| Dependency tree consistent | ✅ | `pip check` |
| No deprecation warnings on import | ✅ | `python -W error::DeprecationWarning -c "import demo"` |
| Unit and route tests | ✅ 11/11 | `python -m pytest -q` |
| Server boots | ✅ | `flask --app demo run`: `GET /` returned 200 and `/static/main.css` returned 200 |
| `upload-images` CLI registered | ✅ | `flask --app demo --help` |
| Upload sends `tags`, `categorization`, `auto_tagging` | ✅ (mocked) | `test_upload_uses_tags_param` |
| Admin API pagination and tag loading | ✅ (mocked) | `test_admin_api_pagination` |
| Live gallery from Cloudinary (`demo` cloud) renders 10 products | ✅ | Live request with no credentials |
| Live delivery URLs (1x and 2x) return `200 image/*` | ✅ | HEAD requests to `res.cloudinary.com` |
| Delivery URLs identical to the original | ✅ | `test_image_url_matches_original_delivery_url` |
| Recommendations exclude the selected items and are ranked by overlap | ✅ | `test_recommend_*` |
| `/output` with no selection shows a validation message | ✅ | `test_output_requires_selection` |
| Cloudinary outage shows an error instead of a 500 | ✅ | `test_catalog_error_is_shown_not_raised` |
| **Live upload, Rekognition tagging and recommendations with real credentials** | ⏳ Not run | Needs a `CLOUDINARY_URL` with the add-on enabled: run `flask --app demo upload-images`, then select a product |
