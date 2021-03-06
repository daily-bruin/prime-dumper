# This script generates Markdown and JSON files from the old prime SQL dump
import sys
import os
import csv
import image_scraper
import urllib.request

# add headers to url lib

def main():
    # define headers for image scraping so we don't get rejected
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0')]
    urllib.request.install_opener(opener)
    # initialize dictionaries that we'll be using to reconstruct tables
    article_list = dict({}) # id is article id
    author_list = dict({}) # id is author id
    issue_list = dict({}) # id is issue id
    image_list = dict({}) # id is image id
    image_list_rel = dict({}) # id 
    # parse the issues table
    with open('./' + 'prime_issue.csv') as csv_issue:
        csv_reader = csv.DictReader(csv_issue)
        for row in csv_reader:
            issue_list.update({row['id']: issue(row['id'], row['name'], row['slug'])})
    # parse the authors table
    with open('./' + 'prime_author.csv') as csv_author:
        csv_reader = csv.DictReader(csv_author)
        for row in csv_reader:
            author_list.update({row['id']: row['first_name'] + ' ' + row['last_name']})
    # parse images table
    with open('./' + 'prime_image.csv') as csv_image:
        csv_reader = csv.DictReader(csv_image)
        for row in csv_reader:
            photo_credit = find_photographer(row['author_id'], author_list)
            print('add image id: ' + row['id'] + ' credit to : ' + photo_credit + '\n')
            toAdd = image(row['id'], row['image'], photo_credit)
            image_list.update({row['id']: toAdd})
            image_list_rel.update({row['image']: toAdd})
    # create image folders so that we can scrape images
    create_image_directories(image_list)
    # parse articles table
    with open('./' + 'prime_article.csv') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            article_list.update({row['id']: article(row['title'], row['slug'], '', issue_list[row['issue_id']].issue_name, row['teaser'], '', row['body'])})
    # parse the article author relation
    with open('./' + 'prime_article_author.csv') as csv_author_article:
        csv_reader = csv.DictReader(csv_author_article)
        for row in csv_reader:
            article_list[row['article_id']].author = author_list[row['author_id']]
    # parse through images in the body text
    # sets the lead_photo to the first photo that appears in the body text
    # and removes that photo from the body
    image_in_body(article_list, image_list)
    
    # open something for writing markdown files
    for key, value in article_list.items():
        with open('./' + value.slug + '.md', 'w') as md_file:
            md_file.write('---\n')
            md_file.write('title: ' + '\'' + value.title + '\'\n')
            md_file.write('author: ' + '\'' + value.author + '\'\n')
            md_file.write('category: ' + '\'' + value.category +'\'\n')
            md_file.write('issue: ' + '\'' + value.issue + '\'\n')
            md_file.write('cover:\n')
            md_file.write('\timg: ' + '\'' + value.lead_image.rel_URL +'\'\n')
            md_file.write('\tauthor: ' + '\'' + value.lead_image.author_name + '\'\n')
            md_file.write('excerpt: ' + '\'' + value.excerpt + '\'\n')
            md_file.write('---\n')
            md_file.write(value.body)
class article:
    def __init__(self, title, slug, author, issue, excerpt, category, body):
        self.title = title
        self.slug = slug
        self.author = author
        self.issue = issue
        self.excerpt = excerpt
        self.category = category
        self.body = body
        self.lead_image = image('','','')
class issue:
    def __init__(self, issue_id, issue_name, issue_slug):
        self.issue_id = issue_id
        self.issue_name = issue_name
        self.issue_slug = issue_slug
class image:
    def __init__(self, image_id, rel_URL, author_name):
        self.image_id = image_id
        self.rel_URL = rel_URL
        self.author_name = author_name

def scrape_lead_image(relative_URL):
    print('fill')
def scrape_image_id(image_id):
    print('fill')
def create_image_directories(image_list):
    for key, value in image_list.items():
        pen_index = value.rel_URL.rfind('/') + 1
        slug_dir = value.rel_URL[0:pen_index]
        if not os.path.exists(slug_dir):
            os.makedirs(slug_dir)

# sets the lead_photo to the first photo that appears in the body text
# and removes that photo from the body
def image_in_body(article_list, image_list):
    for key, value in article_list.items():
        first_photo = True
        while(value.body.find('[img') != -1):
            base_index = value.body.find('[img')
            begin_index = base_index + 4
            end_index = value.body.find(' ', base_index)
            end_bracket = value.body.find(']', base_index)
            position = value.body[end_index + 1:end_bracket]
            image_id = value.body[begin_index : end_index]
            to_replace = value.body[base_index:end_bracket+1]
            replacement_string = '![' + image_list[image_id].author_name + '|' + position + '](' + image_list[image_id].rel_URL + ')'
            # now we can scrape this
            # create the folder if it doesn't exist already                
            print('retrieving: '+ 'http://graphics.dailybruin.com/media/' + image_list[image_id].rel_URL, image_list[image_id].rel_URL)
            urllib.request.urlretrieve('http://graphics.dailybruin.com/media/' + image_list[image_id].rel_URL, image_list[image_id].rel_URL)
            print(to_replace)
            print(replacement_string)
            if first_photo:
                new_body = value.body.replace(to_replace, '')
                new_body.lstrip('\n')
                article_list[key].body = new_body
                article_list[key].lead_image.image_id = image_id
                article_list[key].lead_image.author_name = image_list[image_id].author_name
                article_list[key].lead_image.rel_URL = image_list[image_id].rel_URL
                first_photo = False
            else:
                new_body = value.body.replace(to_replace, replacement_string)
                article_list[key].body = new_body

# returns photographer name from author_id 
def find_photographer(author_id, author_list):
    if author_id in author_list:
        print('adding credit for ' + author_list[author_id] + '\n')
        return author_list[author_id]
    else:
        return ''

main()