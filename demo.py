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

app = Flask(__name__)

def img_upload():
  listOfImgs = os.listdir(os.path.join(os.getcwd()+'/Images'))
  for key,row in enumerate(listOfImgs):
    resp=cloudinary.uploader.upload('Images/'+row,
      categorization = "aws_rek_tagging", 
      auto_tagging = 0.8,
      use_filename = True,
      unique_filename = False,
      overwrite = True,
      folder = "tagged_images",
      transformation = "/c_fill,g_auto,w_250,h_250/f_auto/q_auto",
      tag="my_products"
      )
    print(resp)



@app.route("/", methods=['GET'])
def index():
  # run upload
  #thread = threading.Thread(target=img_upload)
  #thread.start()

  # wait here for the result to be available before continuing
  #thread.join()
  # result = cloudinary.api.resources(type="upload", prefix="tagged_images", max_results=100)
  result = all_images()
  imgs=[]
  count=1
  for asset in result['resources']:
    url="https://res.cloudinary.com/demo/image/upload/v"+str(asset["version"])+"/" +asset["public_id"]
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
    message="Select at least one product image."
    recommendations=[]
  else:
    # Find what were the most frequent tags in the selected product images.
    result = all_images()

    tags=[]
    tag_list=[]
    for img in selected_imgs:
      for asset in result['resources']:
        if asset['public_id']==img:
          img_details = cloudinary.api.resource(img)
          for tag in img_details['tags']:
            #remove irrelevant tags
            if tag != "adult" and tag != "my_products":
              tag_list.append(tag)

    most_frequent_tags=most_frequent(tag_list)



    # Find product images to recommend by matching image tags with the most frequently selected tags.
    recommended_products=[]
    

    for frequent_tag in most_frequent_tags:
      for asset in result['resources']:
        show="yes"
        img_details = cloudinary.api.resource(asset['public_id'])
        for i in selected_imgs:
          if i == asset['public_id']:
            show="no"
          if frequent_tag[0] in img_details['tags'] and show=="yes":
            recommended_products.append(asset['public_id'])
    recommended_products=list(dict.fromkeys(recommended_products))
    

    
    # Send top pictures to recommend
    recommendations=[]
    for prod in recommended_products:
      for asset in result['resources']:
        if asset['public_id']==prod:
          url="https://res.cloudinary.com/demo/image/upload/v"+str(asset["version"])+"/" +asset["public_id"]
          recommendations.append(url)

    message="We thought you might like to try these:"
  return render_template('output.html', recommendations=recommendations, msg=message)

def most_frequent(List):
    c = Counter(List)
    return c.most_common(3)
   
def all_images():
  cloudinary_url("my_products.json", type="list")
  context = ssl._create_unverified_context()
  response = urlopen("https://res.cloudinary.com/demo/image/list/my_products.json", context=context)
  result = json.loads(response.read())
  return result

if __name__ == "__main__":
  app.run()