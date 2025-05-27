import re  
import requests  
from typing import List, Dict, Any, Optional  
from bs4 import BeautifulSoup  
import time  
import random
from requests.adapters import HTTPAdapter  
from urllib3.util.retry import Retry 

class GoogleScholarStandalone:  
    """Standalone Google Scholar search tool without CAMEL dependencies"""  
      
    def __init__(self, timeout: Optional[float] = None, max_retries: int = 3):  
        """Initialize the Google Scholar search tool  
          
        Args:  
            timeout (Optional[float]): Request timeout in seconds, defaults to None  
        """  
        self.timeout = timeout  
        self.headers = {  
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'  
        }  
        
        # 配置重试策略  
        retry_strategy = Retry(  
            total=max_retries,  
            backoff_factor=1,  
            status_forcelist=[429, 500, 502, 503, 504],  
        )  
        adapter = HTTPAdapter(max_retries=retry_strategy)  
        self.session = requests.Session()  
        self.session.mount("https://", adapter)  
        self.session.mount("http://", adapter)  
        
          
    #  Searches for authors on Google Scholar
    def search_author(  
        self,   
        author_name: str,   
        max_results: int = 5  
    ) -> List[Dict[str, Any]]:  
        """Search for authors on Google Scholar  
          
        Args:  
            author_name (str): Name of the author to search for  
            max_results (int): Maximum number of results to return, defaults to 5  
              
        Returns:  
            List[Dict[str, Any]]: List of author information dictionaries  
        """  
        url = f"https://scholar.google.com/citations?view_op=search_authors&mauthors={author_name}&hl=en"  
          
        try:  
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)  
            response.raise_for_status()  
            time.sleep(random.uniform(2, 5))
              
            soup = BeautifulSoup(response.text, 'html.parser')  
            author_elements = soup.select('.gs_ai_chpr')  
              
            results = []  
            for i, author in enumerate(author_elements):  
                if i >= max_results:  
                    break  
                      
                name_elem = author.select_one('.gs_ai_name a')  
                name = name_elem.text if name_elem else "Unknown"  
                  
                profile_url = f"https://scholar.google.com{name_elem['href']}" if name_elem and 'href' in name_elem.attrs else None  
                  
                affiliation = author.select_one('.gs_ai_aff').text if author.select_one('.gs_ai_aff') else "Unknown"  
                  
                cited_by_elem = author.select_one('.gs_ai_cby')  
                cited_by = re.search(r'\d+', cited_by_elem.text).group() if cited_by_elem else "0"  
                  
                interests = [interest.text for interest in author.select('.gs_ai_one_int')]  
                  
                results.append({  
                    "name": name,  
                    "profile_url": profile_url,  
                    "affiliation": affiliation,  
                    "cited_by": cited_by,  
                    "interests": interests  
                })  
                  
            return results  
              
        except Exception as e:  
            print(f"Error searching for author: {e}")  
            return []  
        
    # Gets papers that cite a specific paper  
    def get_citing_papers(  
        self,  
        paper_id: str,  
        max_results: int = 10  
    ) -> List[Dict[str, Any]]:  
        """Get papers that cite a specific paper  
      
        Args:  
            paper_id (str): Google Scholar paper ID (cluster ID)  
            max_results (int): Maximum number of results to return, defaults to 10  
          
        Returns:  
            List[Dict[str, Any]]: List of citing paper information dictionaries  
        """  
        url = f"https://scholar.google.com/scholar?cites={paper_id}&hl=en"  
      
        try:  
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)  
            response.raise_for_status()  
            time.sleep(random.uniform(2, 5))  # 避免被封禁  
          
            soup = BeautifulSoup(response.text, 'html.parser')  
            paper_elements = soup.select('.gs_ri')  
          
            results = []  
            for i, paper in enumerate(paper_elements):  
                if i >= max_results:  
                    break  
                  
                title_elem = paper.select_one('.gs_rt a')  
                title = title_elem.text if title_elem else paper.select_one('.gs_rt').text if paper.select_one('.gs_rt') else "Unknown"  
              
                paper_url = title_elem['href'] if title_elem and 'href' in title_elem.attrs else None  
              
                authors_year_elem = paper.select_one('.gs_a')  
                authors_year_text = authors_year_elem.text if authors_year_elem else ""  
              
                # Extract authors and year  
                authors = re.sub(r'- .*?\d{4}.*', '', authors_year_text).strip() if authors_year_text else "Unknown"  
                year_match = re.search(r'\d{4}', authors_year_text)  
                year = year_match.group() if year_match else "Unknown"  
              
                # Extract abstract  
                snippet = paper.select_one('.gs_rs').text if paper.select_one('.gs_rs') else "No abstract available"  
              
                # Extract citation count  
                cited_by_elem = paper.select_one('a:contains("Cited by")')  
                cited_by = re.search(r'\d+', cited_by_elem.text).group() if cited_by_elem else "0"  
              
                # Extract paper ID for further citation tracking  
                paper_id_match = None  
                if cited_by_elem and 'href' in cited_by_elem.attrs:  
                    paper_id_match = re.search(r'cites=(\d+)', cited_by_elem['href'])  
              
                paper_id = paper_id_match.group(1) if paper_id_match else None  
              
                results.append({  
                    "title": title,  
                    "url": paper_url,  
                    "authors": authors,  
                    "year": year,  
                    "snippet": snippet,  
                    "cited_by": cited_by,  
                    "paper_id": paper_id  
                })  
              
            return results  
          
        except Exception as e:  
            print(f"Error getting citing papers: {e}")  
            return []    
    
    #Searches for papers on Google Scholar
    def search_paper(  
        self,   
        query: str,   
        max_results: int = 10,
        get_citations: bool = False,  
        citations_per_paper: int = 5 
    ) -> List[Dict[str, Any]]:  
        """Search for papers on Google Scholar  
          
        Args:  
            query (str): Search query  
            max_results (int): Maximum number of results to return, defaults to 10  
            get_citations (bool): Whether to fetch papers citing each result, defaults to False  
            citations_per_paper (int): Maximum number of citing papers to fetch per result, defaults to 5 
              
        Returns:  
            List[Dict[str, Any]]: List of paper information dictionaries  
        """  
        url = f"https://scholar.google.com/scholar?q={query}&hl=en"  
          
        try:  
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)  
            response.raise_for_status()  
              
            soup = BeautifulSoup(response.text, 'html.parser')  
            paper_elements = soup.select('.gs_ri')  
              
            results = []  
            for i, paper in enumerate(paper_elements):  
                if i >= max_results:  
                    break  
                      
                title_elem = paper.select_one('.gs_rt a')  
                title = title_elem.text if title_elem else paper.select_one('.gs_rt').text if paper.select_one('.gs_rt') else "Unknown"  
                  
                paper_url = title_elem['href'] if title_elem and 'href' in title_elem.attrs else None  
                  
                authors_year_elem = paper.select_one('.gs_a')  
                authors_year_text = authors_year_elem.text if authors_year_elem else ""  
                  
                # Extract authors and year  
                authors = re.sub(r'- .*?\d{4}.*', '', authors_year_text).strip() if authors_year_text else "Unknown"  
                year_match = re.search(r'\d{4}', authors_year_text)  
                year = year_match.group() if year_match else "Unknown"  
                  
                # Extract abstract  
                snippet = paper.select_one('.gs_rs').text if paper.select_one('.gs_rs') else "No abstract available"  
                  
                # Extract citation count  
                cited_by_elem = paper.select_one('a:contains("Cited by")')  
                cited_by = re.search(r'\d+', cited_by_elem.text).group() if cited_by_elem else "0"  

                 # Extract paper ID for citation tracking  
                paper_id = None  
                if cited_by_elem and 'href' in cited_by_elem.attrs:  
                    paper_id_match = re.search(r'cites=(\d+)', cited_by_elem['href'])  
                    paper_id = paper_id_match.group(1) if paper_id_match else None    

                paper_info = {  
                    "title": title,  
                    "url": paper_url,  
                    "authors": authors,  
                    "year": year,  
                    "snippet": snippet,  
                    "cited_by": cited_by,  
                    "paper_id": paper_id  
                }  
              
                # Fetch citing papers if requested and paper has citations  
                if get_citations and paper_id and int(cited_by) > 0:  
                    time.sleep(random.uniform(2, 5))  # 避免请求过快  
                    paper_info["citing_papers"] = self.get_citing_papers(  
                        paper_id, max_results=citations_per_paper  
                    )  
              
                results.append(paper_info)  
              
            return results  

        except Exception as e:  
            print(f"Error searching for papers: {e}")  
            return []  
    
    # Gets publications for a specific author  
    def get_author_publications(  
        self,   
        author_id: str,   
        max_results: int = 10  
    ) -> List[Dict[str, Any]]:  
        """Get publications for a specific author  
          
        Args:  
            author_id (str): Google Scholar author ID  
            max_results (int): Maximum number of results to return, defaults to 10  
              
        Returns:  
            List[Dict[str, Any]]: List of publication information dictionaries  
        """  
        url = f"https://scholar.google.com/citations?user={author_id}&hl=en"  
          
        try:  
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)  
            response.raise_for_status()  
              
            soup = BeautifulSoup(response.text, 'html.parser')  
            publication_elements = soup.select('tr.gsc_a_tr')  
              
            results = []  
            for i, pub in enumerate(publication_elements):  
                if i >= max_results:  
                    break  
                      
                title_elem = pub.select_one('.gsc_a_at')  
                title = title_elem.text if title_elem else "Unknown"  
                  
                authors_elem = pub.select_one('.gs_gray:nth-of-type(1)')  
                authors = authors_elem.text if authors_elem else "Unknown"  
                  
                venue_elem = pub.select_one('.gs_gray:nth-of-type(2)')  
                venue = venue_elem.text if venue_elem else "Unknown"  
                  
                year_elem = pub.select_one('.gsc_a_y')  
                year = year_elem.text if year_elem else "Unknown"  
                  
                cited_by_elem = pub.select_one('.gsc_a_c')  
                cited_by = cited_by_elem.text if cited_by_elem and cited_by_elem.text.isdigit() else "0"  
                  
                results.append({  
                    "title": title,  
                    "authors": authors,  
                    "venue": venue,  
                    "year": year,  
                    "cited_by": cited_by  
                })  
                  
            return results  
              
        except Exception as e:  
            print(f"Error getting author publications: {e}")  
            return []  
  
# 使用示例  
if __name__ == "__main__":  
    # 创建独立的Google Scholar工具实例  
    scholar = GoogleScholarStandalone(timeout=30)  
      
    # 搜索论文并获取引用信息  
    papers = scholar.search_paper("transformer deep learning", max_results=3, get_citations=True, citations_per_paper=3)  
      
    # 打印结果  
    for i, paper in enumerate(papers):  
        print(f"\n{i+1}. {paper['title']} ({paper['year']})")  
        print(f"   作者: {paper['authors']}")  
        print(f"   被引用次数: {paper['cited_by']}")  
          
        if "citing_papers" in paper and paper["citing_papers"]:  
            print(f"\n   引用该论文的论文:")  
            for j, citing in enumerate(paper["citing_papers"]):  
                print(f"      {j+1}. {citing['title']} ({citing['year']})")  
                print(f"         作者: {citing['authors']}")  
                print(f"         被引用次数: {citing['cited_by']}")