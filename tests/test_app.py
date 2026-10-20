import pytest

import catalog
import demo
from recommender import clean_tags, recommend

CATALOG = [
    {"public_id": "tagged_images/red_dress", "version": 1, "tags": ["my_products", "dress", "red", "adult"]},
    {"public_id": "tagged_images/blue_dress", "version": 2, "tags": ["my_products", "dress", "blue"]},
    {"public_id": "tagged_images/red_heels", "version": 3, "tags": ["my_products", "shoe", "red"]},
    {"public_id": "tagged_images/ring", "version": 4, "tags": ["my_products", "jewelry"]},
    {"public_id": "tagged_images/red_gown", "version": 5, "tags": ["my_products", "dress", "red"]},
]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(catalog, "get_catalog", lambda force_refresh=False: CATALOG)
    demo.app.config["TESTING"] = True
    return demo.app.test_client()


def test_clean_tags_drops_generic_tags():
    assert clean_tags(["my_products", "Adult", "Dress", "dress"]) == ["dress"]


def test_recommend_excludes_selection_and_ranks_by_overlap():
    ids = [r["public_id"] for r in recommend(["tagged_images/red_dress"], CATALOG)]
    assert "tagged_images/red_dress" not in ids
    assert ids[0] == "tagged_images/red_gown"  # shares both "dress" and "red"
    assert "tagged_images/ring" not in ids
    assert set(ids) == {"tagged_images/red_gown", "tagged_images/blue_dress", "tagged_images/red_heels"}


def test_recommend_excludes_every_selected_item():
    ids = [r["public_id"] for r in recommend(["tagged_images/red_dress", "tagged_images/red_gown"], CATALOG)]
    assert "tagged_images/red_gown" not in ids


def test_recommend_unknown_selection_returns_nothing():
    assert recommend(["nope"], CATALOG) == []


def test_image_url_matches_original_delivery_url(monkeypatch):
    monkeypatch.setattr(catalog, "cloud_name", lambda: "demo")
    assert demo.image_url(CATALOG[0]) == (
        "https://res.cloudinary.com/demo/image/upload/f_auto/q_auto/"
        "c_fill_pad,g_auto,w_100,h_100/v1/tagged_images/red_dress"
    )


def test_index_renders_gallery(client):
    html = client.get("/").get_data(as_text=True)
    assert html.count('name="selected_imgs"') == len(CATALOG)
    assert "w_200,h_200" in html and 'loading="lazy"' not in html.split("myCheckbox5")[0]


def test_output_requires_selection(client):
    assert "Select at least one product image." in client.post("/output").get_data(as_text=True)


def test_output_shows_recommendations(client):
    html = client.post("/output", data={"selected_imgs": ["tagged_images/red_dress"]}).get_data(as_text=True)
    assert "We thought you might like to try these:" in html
    assert "v5/tagged_images/red_gown" in html
    assert "v1/tagged_images/red_dress" not in html


def test_catalog_error_is_shown_not_raised(monkeypatch):
    def boom(force_refresh=False):
        raise RuntimeError("network down")
    monkeypatch.setattr(catalog, "get_catalog", boom)
    resp = demo.app.test_client().get("/")
    assert resp.status_code == 200 and "Could not load products" in resp.get_data(as_text=True)


def test_admin_api_pagination(monkeypatch):
    pages = [
        {"resources": [{"public_id": "a", "tags": ["x"]}], "next_cursor": "c1"},
        {"resources": [{"public_id": "b"}]},
    ]
    calls = []
    def fake(tag, **opts):
        calls.append(opts)
        return pages[len(calls) - 1]
    monkeypatch.setattr(catalog, "has_api_credentials", lambda: True)
    monkeypatch.setattr(catalog.cloudinary.api, "resources_by_tag", fake)
    result = catalog.fetch_catalog()
    assert [r["public_id"] for r in result] == ["a", "b"]
    assert result[1]["tags"] == []
    assert calls[0]["tags"] is True and calls[1]["next_cursor"] == "c1"


def test_upload_uses_tags_param(monkeypatch, tmp_path):
    (tmp_path / "shoe.jpg").write_bytes(b"x")
    (tmp_path / ".DS_Store").write_bytes(b"x")
    calls = []
    monkeypatch.setattr(demo, "IMAGES_DIR", str(tmp_path))
    monkeypatch.setattr(demo.cloudinary.uploader, "upload",
                        lambda path, **opts: calls.append(opts) or {"public_id": "tagged_images/shoe", "tags": opts["tags"]})
    demo.img_upload()
    assert len(calls) == 1
    assert calls[0]["tags"] == ["my_products"] and calls[0]["categorization"] == "aws_rek_tagging"
