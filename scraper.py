import re
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
import time
from collections import namedtuple
from urllib import robotparser


visited_urls = []                                # List of all urls that have been visited
check_dynamic_traps_query = set()                # Set of sliced querys to check for dynamic traps
date_terms = {"past", "day", "month", "year"} # Set of date terms
index_content = []                              # Index content of redirected URLs

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
#question 1 and question 2
unique_pages_found = dict()#http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL. # link='', word_count=0
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
    
    #note that one megabyte is equal to 1024 * 1024
    global visited_urls
    
    extracted_links = set()
    if resp.status == 200 and resp.raw_response.content and len(resp.raw_response.content) < 10 * 1024 * 1024:
            page_content = BeautifulSoup(resp.raw_response.content,'html.parser').get_text()
            page_tokens = my_tokenize(page_content)
            if len(page_tokens) > 100:

                create_subdomain_dictionary(url)    # Answers Q4 by checking each subdomain
                update_word_frequency(page_tokens)

                for link in BeautifulSoup(resp.raw_response.content, 'html.parser').find_all('a', href=True):
                    absolute_link = link['href']
                    if absolute_link != url and absolute_link not in visited_urls:
                        visited_urls.append(absolute_link)
                        update_unique_pages_found(url, len(page_tokens))
                        extracted_links.add(absolute_link)

    elif resp.status == 301 or resp.status == 302:
        index_content.append(url)
        list_as_string = ', '.join(map(str, index_content))

    else:
        print("ERROR", resp.error)

    return list(extracted_links)


def my_tokenize(text_content):
    # this is Santiago's tokenize for assingmnet1 modefied to work for this assignment
    # Tokens are all alphanumeric characters
    token_list = list()
    for word in re.findall('[^a-zA-Z0-9]', text_content):
        print("token: " + word)
        if word.lower() not in stop_words:
            token_list.append(word.lower())
    return token_list


def is_ics_uci_edu_subdomain(link):
    '''
    Checks if the subdomain is ics.uci.edu
    '''
    hostInfo = urlparse(link).hostname
    return re.match(r'(?:http?://|https?://).*\.ics\.uci\.edu', hostInfo)
    
    
def create_subdomain_dictionary(url):
    '''
    Parses the URL and checks to see if the hostname 
    is in the subdomain dictionary. If so, then the count
    for the subdomain increases count by 1, else, makes it a 
    key and sets it to 1.
    '''
    global subdomain_and_numpages
    parsed_hostname = urlparse(url).hostname
    print(parsed_hostname)

    if is_ics_uci_edu_subdomain(url):
        if parsed_hostname in subdomain_and_numpages:
            subdomain_and_numpages[parsed_hostname] += 1
        else:
            subdomain_and_numpages[parsed_hostname] = 1


def update_word_frequency(tokens):
    global words_and_frequency
    for token in tokens:
        if token not in words_and_frequency:
            words_and_frequency[token] = 1
        else:
            words_and_frequency[token] += 1


def update_unique_pages_found(link, other_word_count):
    global unique_pages_found
    link = remove_fragment(link)
    if link in unique_pages_found:
        unique_pages_found[link] += other_word_count
    else:
        unique_pages_found[link] = other_word_count


def remove_fragment(url):
    parsed_url = urlparse(url)
    url_without_fragment = parsed_url._replace(fragment='')
    reconstructed_url = urlunparse(url_without_fragment)
    return reconstructed_url


def read_robots(url, user_agent='IR UW24 34909351,23919089'):
    '''
    Reads robots.txt and deems if it is 
    allowed to be crawled to.
    '''
    print("robot.txt will be read")
    rp = robotparser.RobotFileParser()      # Parses robot.txt
    rp.set_url(url + '/robots.txt')         # Set the URL of the robots.txt file
    rp.read()                               # Read and parse the robots.txt file
    print("robot.txt is read")
    return rp.can_fetch(user_agent, url)    # Searches robots.txt and returns boolean if site can be crawled


def dynamic_trap_check(parsed):
    '''
    Checks if URL is a Dynamic Trap but looking 
    into matching keywords.
    ''' 
    print("dynamic trap will start")
    url_query = parsed.query
    index = url_query.index("=")
    new_url_query = parsed.hostname + parsed.path + "?" + url_query[0:index]  # Rebuilds the url but with only the first parameter

    if new_url_query in check_dynamic_traps_query:          # Checks if the URL is already been crawled through
        print("dynamic trap")
        return True
    else:
        check_dynamic_traps_query.add(new_url_query)
        print("not dynamic trap")
        return False


def calendar_trap_check(parsed, path_segments):
    '''
    Checks for any URLs that are calendar traps.
    '''
    print("calendar check will start")
    date_pattern = re.compile(r'/(?:(?:\d{2,4}-\d{2}-\d{2,4})|(?:\d{2,4}-\d{2,4})|(?:\d{1,2}/\d{1,2}/\d{2,4}))/')

    if re.match(date_pattern, parsed.path) or bool(set(path_segments) & date_terms):    # Check if there is a number date format in the URL
        return True
    print("calendar ending")
    return bool(set(parsed.query) & date_terms) # Checks for evenDisplay=past to avoid going too deep into calendar


def is_trap(url, parsed):
    '''
    Checks if url is a trap, returns true if so
    else returns false.
    Covers:
        - Duplicate URL Traps
        - Repeated Paths Trap (ICS Calendar)
        - Session ID Trap
        - Dynamic URL Trap
    '''
    print("is_valid is starting")
    path_segments = parsed.path.lower().split("/")
    
    if url in visited_urls:                                         # Covers Duplicate URL Traps by checking already visited URLs
        print("it is a visited url trap")
        return True  
    
    elif len(path_segments) != len(set(path_segments)):             # Checks for any repeating paths
        print("it is a repeating path url trap")
        return True
        
    elif "session" in path_segments or "session" in parsed.query:   # Check for Session ID traps
        print("it is a session ID trap")
        return True

    return dynamic_trap_check(parsed) or calendar_trap_check(parsed, path_segments) # Covers Dynamic URL Trap by checking for duplicate params
                                                                                    # and Covers Calendar Trap by checking repeating paths


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
        pattern = re.compile(r"(?:http?://|https?://)?(?:ics|cs|informatics|stat)\.uci\.edu\/S*")

        if parsed.scheme in set(["http", "https"]) and re.match(pattern, url.lower()):  # Checks if URL matches the requirements
            if read_robots(url):                # Checks if robots.txt allows crawlers
                if not is_trap(url, parsed):    # Check if the URL is a trap
                    return not re.match(
                        r".*.(css|js|bmp|gif|jpe?g|ico"
                        + r"|png|tiff?|mid|mp2|mp3|mp4"
                        + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                        + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                        + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                        + r"|epub|dll|cnf|tgz|sha1"
                        + r"|thmx|mso|arff|rtf|jar|csv"
                        + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        return False
    
    except TypeError:
        print ("TypeError for ", parsed)
        raise

def generate_report_txt():
    with open('report.txt', 'w') as report:
        print("number of unique pages found: "+ str(len(unique_pages_found.keys())))

        report.write("------------------Report------------------"+ "\n")
        report.write("" + "\n")

        report.write("------------------QUESTION #1------------------"+"\n")
        report.write("Unique pages found: " + str(len(unique_pages_found.keys())) + "\n")
        report.write("" + "\n")
        report.write("" + "\n")

        report.write("------------------QUESTION #2------------------"+"\n")
        report.write("URL with the largest word count: "+ max(unique_pages_found, key=unique_pages_found.get) + "\n")
        report.write("" + "\n")
        report.write("" + "\n")

        report.write("------------------QUESTION #3------------------"+"\n")
        report.write("The following are the 50 most common words")
        top_50_words = sorted(words_and_frequency.items(), key=lambda item: item[1], reverse=True)[:50]
        for word, frequency in top_50_words:
            report.write(f"Word: {word}, Frequency: {frequency}" + "\n")
        report.write("" + "\n")
        report.write("" + "\n")

        report.write("------------------QUESTION #4------------------"+"\n")
        report.write("Number of subdomains in the ics.uci.edu domain: " + str(len(subdomain_and_numpages.keys())))
        sorted_subdomains = sorted(subdomain_and_numpages.keys())
        for subdomain in sorted_subdomains:
            num_pages = subdomain_and_numpages[subdomain]
            print(f"{subdomain}, {num_pages}")
        report.write("" + "\n")
        report.write("" + "\n")
        