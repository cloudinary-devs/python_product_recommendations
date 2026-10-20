# 🛍️ Cloudinary Product Recommendation App

The Cloudinary Product Recommendation App is a Python Flask web app that recommends similar e-commerce products by ranking the AI-generated tags that Cloudinary's Amazon Rekognition Auto Tagging add-on (`aws_rek_tagging`, `auto_tagging`) attaches at upload, then serves a responsive product grid with `f_auto`, `q_auto`, `c_fill_pad` and `g_auto`.

## ✨ Features

- 🏷️ Upload a folder of product photos and let Cloudinary tag each one with AI.
- 🧠 Select one or more products and get recommendations ranked by how many AI tags they share with your selection.
- 🖼️ Fluid product grid: columns reflow to any screen width, thumbnails lazy-load, and high-DPI screens get a 2x image.
- ⚡ The whole catalog and its tags load in one paginated Admin API call and are cached in memory.

## Cloudinary features used

- `categorization: "aws_rek_tagging"` — runs the Amazon Rekognition Auto Tagging add-on on each upload to detect objects and scenes in the image
- `auto_tagging: 0.8` — adds every detected label with at least 80% confidence as a tag on the asset
- `tags` — adds the `my_products` tag to every upload so the whole catalog can be listed by tag
- `folder`, `use_filename`, `unique_filename`, `overwrite` — stores uploads as `tagged_images/<filename>` and replaces them on re-upload
- Incoming `transformation` (`c_fill,g_auto,w_250,h_250`) — crops the stored original to a 250×250 square around the main subject at upload
- `resources_by_tag` (Admin API, `tags=True`) — returns every `my_products` asset with its tags in one paginated request
- Client-side resource list (`/image/list/my_products.json`) — lists tagged assets without credentials (used as a fallback for the gallery)
- `f_auto` — automatically serves WebP or AVIF based on the visitor's browser
- `q_auto` — picks the lowest file size that keeps visual quality
- `c_fill_pad` with `g_auto` — fills the 100×100 tile around the detected subject, padding instead of cutting the product off
- `w_` / `h_` responsive variants — 100px and 200px versions feed the `srcset` so retina screens get sharp thumbnails

## Use cases

- You run an online store and want a "you might also like" row without building or training a custom ML model.
- You have a large product image library with no metadata and need it tagged automatically so it can be searched, filtered or grouped.
- You want an example of feeding Cloudinary AI tags into a Python data pipeline that you can later swap for a more advanced model.

## 🛠 Tech Stack

- [Python 3.12+](https://www.python.org/) with [Flask 3.1](https://flask.palletsprojects.com/) – web server and templates
- [Cloudinary Python SDK 1.46](https://cloudinary.com/documentation/django_integration) – uploads, Admin API and delivery URLs
- [Amazon Rekognition Auto Tagging add-on](https://cloudinary.com/documentation/aws_rekognition_auto_tagging_addon) – AI tags
- [Tailwind CSS](https://tailwindcss.com/) (CDN) – page styling

## 🛠 Environment Variables

Create a `.env` file at the root of the project (you can copy `.env.example`):

```
CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>

# Optional: seconds to cache the product catalog (default 300)
CATALOG_CACHE_TTL=300
```

- `CLOUDINARY_URL` (required for uploads and recommendations): copy the **API environment variable** value from the [API Keys](https://console.cloudinary.com/settings/api-keys) page of the Cloudinary Console. The app reads your cloud name, API key and API secret from it.
- `CATALOG_CACHE_TTL` (optional): how long, in seconds, the product list and its tags are cached before the app asks Cloudinary again.

If `CLOUDINARY_URL` isn't set, the homepage still shows the public `demo` cloud's products, but recommendations are turned off because tags need the Admin API.

> **Note:** Never commit your `.env` file. It's already listed in `.gitignore`.

## ☁️ Cloudinary account setup

1. [Sign up](https://cloudinary.com/users/register_free) for a free Cloudinary account.
2. In the Console, go to **Settings → Add-ons** ([direct link](https://console.cloudinary.com/settings/addons)), find **Amazon Rekognition Auto Tagging** and subscribe to the free plan.
3. Go to **Settings → Security** and, under **Restricted media types**, make sure **Resource list** is _not_ checked. This allows the credential-free list fallback.
4. Copy your **API environment variable** from **Settings → API Keys** into `.env` as `CLOUDINARY_URL`.

## 🚀 Running the App

1. **Clone the repository:**
   ```sh
   git clone https://github.com/cloudinary-devs/python_product_recommendations.git
   cd python_product_recommendations
   ```
2. **Create a virtual environment with Python 3.12 or later:**
   ```sh
   python3.12 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set up your `.env` file** as described above.
5. **Upload and auto-tag the product images** in the `Images` folder (run this once, or again after adding images):
   ```sh
   flask --app demo upload-images
   ```
6. **Start the development server:**
   ```sh
   flask --app demo run
   ```
   You can also run `python demo.py`. Set the `PORT` variable to change the port.
7. **Open your browser** at [http://localhost:5000](http://localhost:5000), select at least one product and click **Submit**.

## 🔍 How It Works

1. **Upload (`flask --app demo upload-images`)**: every image in `Images/` is uploaded to the `tagged_images` folder with the `my_products` tag. Amazon Rekognition adds AI tags at the same time.
2. **Catalog pipeline (`catalog.py`)**: one paginated `resources_by_tag` call loads every product with its tags. The result is cleaned up and cached for `CATALOG_CACHE_TTL` seconds.
3. **Homepage (`/`)**: shows the first 10 products in a responsive grid of checkboxes.
4. **Recommendation model (`recommender.py`)**: the 3 most frequent tags in your selection form a profile. Every other product that shares at least one of those tags is scored by how often its matching tags appear in the selection, and the results are sorted by that score.
5. **Recommendations page (`/output`)**: shows the ranked products. Hover over an image to see which tags matched.

## 📁 Key Files

- `demo.py`: Flask app with the routes, the `upload-images` command and the delivery URL builder.
- `catalog.py`: loads the catalog and AI tags from Cloudinary and caches them.
- `recommender.py`: tag-based scoring and ranking. It has no dependencies, so you can test it on its own.
- `templates/index.html`: product selection grid.
- `templates/output.html`: recommended products grid.
- `static/main.css`: grid and selection styles.
- `tests/test_app.py`: unit and route tests. Cloudinary is mocked, so no account is needed.

## ✅ Testing

```sh
pip install -r requirements-dev.txt
python -m pytest -q
pip-audit -r requirements.txt
```
