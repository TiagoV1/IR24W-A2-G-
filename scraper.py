import re
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
import time
from collections import namedtuple

global stop_words
stop_words = ('a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't",
              'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
              "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't",
              'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have',
              "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him',
              'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't",
              'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor',
              'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out',
              'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some',
              'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
              "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to',
              'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were',
              "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's",
              'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're",
              "you've", 'your', 'yours', 'yourself', 'yourselves')
#question 1
unique_pages_found = set()#http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL.
#question 2
current_longest_page_template = namedtuple('current_longest_page', ['link', 'word_count'])
longest_page = current_longest_page_template(link='', word_count=0)
#question 3
words_and_frequency = dict()
#question 4
subdomain_and_numpages = dict() # subdomain as key, pages count as value

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    extracted_links = set()
    if resp.status == 200 and resp.raw_response.content:
            page_content = BeautifulSoup(resp.raw_response.content,'html.parser').get_text()
            page_tokens = my_tokenize(page_content)
            if len(page_tokens) > 100:
                if is_ics_uci_edu_subdomain(url):
                    subdomain_and_numpages[url] = 0# this is temporary because idk how to increase the count correctly
                
                if is_new_longest_page(url, len(page_tokens)):
                    longest_page = current_longest_page_template(link=url, word_count=len(page_tokens))

                update_word_frequency(page_tokens)

                extracted_links = page_content.find_all('a')
                for link in BeautifulSoup(resp.raw_response.content, 'html.parser').find_all('a', href=True):
                    absolute_link = link['href']
                    absolute_link = remove_fragment(absolute_link)
                    unique_pages_found.add(absolute_link)
                    extracted_links.add(absolute_link)
    else:
        print("ERROR", resp.error)
    time.sleep(2)
    return list(extracted_links)

def my_tokenize(text_content):
    # this is Santiago's tokenize for assingmnet1 modefied to work for this assignment
    # Tokens are all alphanumeric characters
    token_list = list()
    for word in re.findall('[^a-zA-Z0-9]', text_content):
        if word.lower() not in stop_words:
            token_list.append(word.lower())
    return token_list


def is_ics_uci_edu_subdomain(link):
    # this function will help answer questions 4 and 1
    # it checks if the subdomain is ics.uci.edu
    hostInfo = urlparse(link).hostname
    return hostInfo.endswith('ics.uci.edu')

def update_word_frequency(tokens):
    global words_and_frequency
    for token in tokens:
        if token not in words_and_frequency:
            words_and_frequency[token] = 1
        else:
            words_and_frequency[token] += 1

def is_new_longest_page(other_link, other_word_count):
    global longest_page
    if other_link == longest_page.link:
        return False
    if other_word_count > longest_page.word_count:
        return True
    return False

def remove_fragment(url):
    parsed_url = urlparse(url)
    url_without_fragment = parsed_url._replace(fragment='')
    reconstructed_url = urlunparse(url_without_fragment)
    return reconstructed_url

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    # *.ics.uci.edu/*
    # *.cs.uci.edu/*
    # *.informatics.uci.edu/*
    # *.stat.uci.edu/*

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        pattern = re.compile(r"(?:http?://|https?://)?(?:ics|cs|informatics|stat)\.uci\.edu\/S*")
        if re.match(pattern, parsed.path.lower()):
            return True
        return False

    except TypeError:
        print ("TypeError for ", parsed)
        raise
