# read from .env file
from dotenv import load_dotenv
load_dotenv()

# import Cloudinary libraries
import cloudinary
from cloudinary import uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url

# import other libraries
import os
import threading
from collections import Counter
from urllib.request import urlopen
import ssl
import json

# get reference to config instance
# config = cloudinary.Config()
# print(config.cloud_name)
# print(config.api_key)

from flask import Flask, render_template, request
import json

app = Flask(__name__, static_url_path='/static')

def img_upload():
  # Get your images stored in a local directory.
  listOfImgs = os.listdir(os.path.join(os.getcwd()+'/Images'))

  # Upload all those images to Cloudinary with auto-tagging.
  for key,row in enumerate(listOfImgs):
    resp=cloudinary.uploader.upload('Images/'+row,
      categorization = "aws_rek_tagging", 
      auto_tagging = 0.8,
      use_filename = True,
      unique_filename = False,
      overwrite = True,
      folder = "tagged_images",
      transformation = "/c_fill,g_auto,w_250,h_250/f_auto/q_auto",
      # You’ll use the my_products tag to retrieve all the images.
      tag="my_products"
      )


@app.route("/", methods=['GET'])
def index():
  # Only call the img_upload function to upload your images the first time you run this program.

  # thread = threading.Thread(target=img_upload)
  # thread.start()

  # wait here for the result to be available before continuing
  # thread.join()
 
  # Get all the images you uploaded and display the first ten of them in ‘index.html’.  
  result = all_images()
  imgs=[]
  count=1
  for asset in result['resources']:
    # Build the delivery URL for the asset. 
    url="https://res.cloudinary.com/demo/image/upload/f_auto/q_auto/c_fill_pad,g_auto,w_100,h_100/v"+str(asset["version"])+"/" +asset["public_id"]
    # Add image information, including image url and public ID,  to an array for displaying all the images
    # in index.html.
    img_entry={'url':url, 'id':"myCheckbox"+str(count), 'public_id':asset['public_id']}
    imgs.append(img_entry)
    if count==10:
      break
    count+=1
    
  return render_template('index.html', imgs=imgs)


@app.route("/output", methods=['POST'])
def output():
    selected_imgs = request.form.getlist("selected_imgs")
    if not selected_imgs:
        message = "Select at least one product image."
        recommendations = []
    else:
        result = all_images()
        tag_list = []
        for img in selected_imgs:
            for asset in result['resources']:
                if asset['public_id'] == img:
                    img_details = cloudinary.api.resource(img)
                    tag_list.extend(tag for tag in img_details['tags'] if tag not in ["adult", "my_products"])
        most_frequent_tags = most_frequent(tag_list)
        recommendations = []
        for frequent_tag in most_frequent_tags:
            for asset in result['resources']:
                show = "yes"
                img_details = cloudinary.api.resource(asset['public_id'])
                for i in selected_imgs:
                    if i == asset['public_id']:
                        show = "no"
                    if frequent_tag[0] in img_details['tags'] and show == "yes":
                        url="https://res.cloudinary.com/demo/image/upload/f_auto/q_auto/c_fill_pad,g_auto,w_100,h_100/v"+str(asset["version"])+"/" +asset["public_id"]         
                        if url not in recommendations:
                            recommendations.append(url)
        message = "We thought you might like to try these:"
    return render_template('output.html', recommendations=recommendations, msg=message)

def most_frequent(List):
    c = Counter(List)
    return c.most_common(3)
   
def all_images():
  # Return a JSON with  all the images you uploaded using the cloudinary_url method from the
  # cloudinary.utils library. 
  # You can also use the resources method from the admin API (rate-limited).
  cloudinary_url("my_products.json", type="list")
  context = ssl._create_unverified_context()
  response = urlopen("https://res.cloudinary.com/demo/image/list/my_products.json", context=context)
  result = json.loads(response.read())
  return result

if __name__ == "__main__":
  app.run()