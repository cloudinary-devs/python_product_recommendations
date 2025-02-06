Cloudinary Product Recommendation App
======================================================

This is a Flask-based application that uses Cloudinary's API for image management, tagging, and generating image recommendations based on user-selected content.

## Features

* **Image Upload**: Automatically uploads images from a local directory to Cloudinary, tagging them with AI-powered categorization (AWS Rekognition).
* **Dynamic Recommendations**: Suggests additional images based on shared tags with user-selected images.
* **Optimized Image Display**:
  * Images are transformed dynamically for consistent quality and format.
  * Delivered via Cloudinary’s CDN for optimal performance.

## How It Works

1. **Image Upload**:
    * Images in the `Images` directory are uploaded to Cloudinary with auto-tagging enabled.
    * Images are stored in a `tagged_images` folder with relevant tags.
2. **Homepage (/)**:
    * Displays up to 10 uploaded images.
    * Users can select images to receive recommendations.
3. **Recommendations Page (/output)**:
    * Based on selected images, the app analyzes tags and suggests similar images.

## Running the App

### Use It on Glitch

You can use [this app](https://glitch.com/edit/#!/python-product-recommendations) without any setup!

### Use Your Own Product Environment

However, if you want to work off of your own product environment:

* [Sign up](https://cloudinary.com/users/register_free) for a free Cloudinary account.
* [Register](https://console.cloudinary.com/settings/addons) for the [Google Tagging](https://cloudinary.com/documentation/google_auto_tagging_addon) and [Amazon Rekognition AI Moderation](https://cloudinary.com/documentation/aws_rekognition_ai_moderation_addon) add-ons. 

#### Remix on Glitch (optional)

1. **Remix** it on Glitch.
2. Enter your **API Environment Variable** value (can be found on the [API Keys](https://console.cloudinary.com/settings/api-keys) page of the Cloudinary Console) in the `.env` file of your Glitch directory.
3. Place images in an `Images` folder at the root of the project.

### Run Locally (Optional)

1. Clone this [GitHub](https://github.com/cloudinary-devs/python_product_recommendations) repository.
2. Install the required Python packages:
   ```bash
   pip install flask cloudinary requests
   ```
3. Place images in an `Images` folder at the root of the project.
4. Run the app.

## Key Files

* `app.py`: Core Flask app handling routing, image uploads, and recommendations.
* `templates/index.html`: Displays uploaded images for selection.
* `templates/output.html`: Shows recommended images based on user-selected tags.

## Dependencies

This app uses the following libraries:

* **Flask**: Python web framework.
* **[Cloudinary](https://cloudinary.com/)**: For image management and transformations.
* `urllib3`: HTTP client for accessing Cloudinary lists.
* `collections`: For counting tag frequencies.
* `ssl`: For handling secure HTTP requests.

