from bitflow.utils.module import Module

'''
WARNING: Some of the following code disobeys robots.txt of particular websites.
  Thus, it is disabled by default and only left as reference.
  Use at your own risk.

       o     O
     __|_____|___
    |    --      |
    |  ( o )   ( o )
  { |        /   |
    |     [wwww]  < *Exterminate all humans.txt* )
    [____________|
       |   |              /Vvvv/
  _____|___|____          |___/
 /______________\_________/   |
 |              |             /
 | ( / )  ( + ) |__|__|__|_|_/
 |              |
 | [ -vV--vV-]  |
 |              |
 |______________/
'''

def process_section(section):
    '''
    A trivial helper function. Genuinely not sure why I thought this helped...
    '''
    paragraphs = section.find_all('p')
    return '\n'.join(p.get_text() for p in paragraphs)

class JEBModule(Module):
    '''
    Download Articles from the Journal of Experimental Biology
    '''
    def __init__(self, in_label='Taxon', out_label='JEBArticle:Article', connect_labels=('MENTIONED_IN_ARTICLE', 'MENTIONS_SPECIES'), name='JEB'):
        Module.__init__(self, in_label, out_label, connect_labels, name)
        self.JEB_LIMIT = 50

    def process(self, previous):
        '''
        Download JEB articles for a taxon.
        Simple HTML parser..

        :param previous: neo4j transaction representing a Taxon.
        '''
        from bs4      import BeautifulSoup 
        from requests import get
        from pprint import pprint
        name   = previous.data['name']
        url    = 'https://jeb.biologists.org/search/' + name.replace(' ', '%252B')
        result = get(url)
        soup   = BeautifulSoup(result.content, 'html.parser')
        articles = []
        article_links = ['https://jeb.biologists.org' + x.get('href') for x in soup.find_all('a', attrs={'class': 'highwire-cite-linked-title'})]
        i = 0
        for article_link in article_links:
            try:
                if i == self.JEB_LIMIT:
                    break
                article_page = BeautifulSoup(get(article_link).content, 'html.parser')
                category     = article_page.find(attrs={'class' : 'highwire-cite-category'}).get_text()
                if category == 'Research Article':
                    properties = dict()
                    properties['url']  = article_link
                    properties['title']    = article_page.find(attrs={'class' : 'highwire-cite-title'}).get_text()
                    properties['authors']  = article_page.find(attrs={'class' : 'highwire-cite-authors'}).get_text()
                    article_page = article_page.find(attrs={'class' : 'fulltext-view'})
                    sections = [process_section(section) for section in article_page.find_all(attrs={'class' : 'section'})]
                    properties['abstract'] = sections[0]
                    properties['intro']    = sections[1]
                    properties['methods']  = sections[2]
                    properties['results']  = sections[3]
                    properties['content']  = '\n'.join(sections[1:])
                    articles.append(self.default_transaction(properties, uuid=properties['title'] + '_JEBArticle', from_uuid=previous.uuid))
                    i += 1
            except AttributeError:
                pass
        return articles
