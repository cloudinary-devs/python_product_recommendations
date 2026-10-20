# read from .env file
from dotenv import load_dotenv
load_dotenv()

# import Cloudinary libraries
import cloudinary
from cloudinary import uploader
from cloudinary import CloudinaryImage

# import other libraries
import logging
import os

import click
from flask import Flask, render_template, request

import catalog
from recommender import recommend

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, 'Images')
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')

# Number of products shown on the homepage.
GALLERY_SIZE = 10
# Displayed size (CSS pixels) of each product thumbnail.
THUMB_SIZE = 100


def img_upload():
  # Get your images stored in a local directory.
  listOfImgs = sorted(f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(IMAGE_EXTENSIONS))

  # Upload all those images to Cloudinary with auto-tagging.
  for row in listOfImgs:
    resp = cloudinary.uploader.upload(os.path.join(IMAGES_DIR, row),
      categorization = "aws_rek_tagging",
      auto_tagging = 0.8,
      use_filename = True,
      unique_filename = False,
      overwrite = True,
      folder = "tagged_images",
      transformation = "/c_fill,g_auto,w_250,h_250/f_auto/q_auto",
      # You’ll use the my_products tag to retrieve all the images.
      tags = [catalog.PRODUCT_TAG]
      )
    log.info("Uploaded %s with tags: %s", resp['public_id'], ', '.join(resp.get('tags', [])))

  # New uploads should show up on the next request.
  catalog.clear_cache()


@app.cli.command("upload-images")
def upload_images_command():
  """Upload everything in Images/ to Cloudinary with AI auto-tagging."""
  img_upload()
  click.echo("Upload complete.")


def image_url(asset, size=THUMB_SIZE):
  # Build the delivery URL for the asset: f_auto/q_auto pick the best format and
  # quality for the browser, and c_fill_pad with g_auto keeps the product in frame.
  return CloudinaryImage(asset['public_id']).build_url(
    cloud_name=catalog.cloud_name(),
    secure=True,
    version=asset.get('version'),
    transformation=[
      {'fetch_format': 'auto'},
      {'quality': 'auto'},
      # Raw string keeps the original w_,h_ order so already-derived images are reused.
      {'raw_transformation': f'c_fill_pad,g_auto,w_{size},h_{size}'},
    ],
  )


def image_entry(asset, index):
  # Image information for the templates, including a 2x variant for high-DPI screens.
  return {
    'url': image_url(asset),
    'srcset': f"{image_url(asset)} 1x, {image_url(asset, THUMB_SIZE * 2)} 2x",
    'id': "myCheckbox" + str(index),
    'public_id': asset['public_id'],
    'tags': asset.get('matched_tags', []),
  }


def load_catalog():
  try:
    return catalog.get_catalog(), None
  except Exception:
    log.exception("Could not load the product catalog from Cloudinary")
    return [], "Could not load products from Cloudinary. Check your CLOUDINARY_URL and try again."


@app.route("/", methods=['GET'])
def index():
  # To upload your images the first time you run this program, run: flask --app demo upload-images

  # Get all the images you uploaded and display the first ten of them in ‘index.html’.
  assets, error = load_catalog()
  imgs = [image_entry(asset, count) for count, asset in enumerate(assets[:GALLERY_SIZE], start=1)]
  return render_template('index.html', imgs=imgs, error=error, thumb_size=THUMB_SIZE)


@app.route("/output", methods=['POST'])
def output():
    selected_imgs = request.form.getlist("selected_imgs")
    recommendations = []
    if not selected_imgs:
        message = "Select at least one product image."
    else:
        assets, error = load_catalog()
        if error:
            message = error
        else:
            # Rank the rest of the catalog by the selection's most frequent AI tags.
            ranked = recommend(selected_imgs, assets)
            recommendations = [image_entry(asset, count) for count, asset in enumerate(ranked, start=1)]
            message = "We thought you might like to try these:"
            if not recommendations and not catalog.has_api_credentials():
                message = "Recommendations need AI tags. Set CLOUDINARY_URL to load them with the Admin API."
            elif not recommendations:
                message = "No similar products found. Try selecting a different product."
    return render_template('output.html', recommendations=recommendations, msg=message, thumb_size=THUMB_SIZE)


if __name__ == "__main__":
  app.run(port=int(os.environ.get("PORT", 5000)))
