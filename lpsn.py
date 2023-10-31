# 导入必要的库
import requests  # 用于发送HTTP请求
from bs4 import BeautifulSoup  # 用于解析HTML内容
from urllib.parse import urljoin, urlparse
import os
import pandas as pd
from tqdm import tqdm

# 定义目标URL
BASE_URL = "https://lpsn.dsmz.de/"
SPECIES_URL = "https://lpsn.dsmz.de/species"

def generate_base_url(url):
    # SPECIES_URL = https://lpsn.dsmz.de/species
    # ParseResult(scheme='https', netloc='lpsn.dsmz.de', path='/species', params='', query='', fragment='')
    parsed_url = urlparse(url)

    # "https://lpsn.dsmz.de/"
    new_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    return new_base_url

def generate_url_with_page(url) -> tuple[str, list]:
    alphabet_list = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    params_list: list[dict[str: str]] = []
    for alphabet in alphabet_list:
        params_list.append({'page': alphabet})
    return url, params_list

def soup_extract(url: str, params: dict = None):
      # 定义一个伪装的浏览器User-Agent头，以避免某些网站阻止程序访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 使用requests库发送GET请求到指定URL
    if params:
        response = requests.get(url, headers=headers, params=params)
    else:
        response = requests.get(url, headers=headers)
    
    # 如果HTTP响应代码不是200（表示请求成功），则输出错误消息并返回空列表
    if response.status_code != 200:
        print("Failed to fetch the page!")
        return []

    # 使用BeautifulSoup解析HTTP响应的内容
    soup = BeautifulSoup(response.content, 'html.parser')

    return soup


# 定义一个函数，用于从给定的URL中提取物种名称
def fetch_species_href(url: str, params: dict):
    # 构建新的基础URL
    # url = https://lpsn.dsmz.de/species
    # new_base_url = https://lpsn.dsmz.de/
    new_base_url = generate_base_url(url=url)

    sepecies_soup = soup_extract(url=url, params=params)  

    main_list = sepecies_soup.select_one('ul.main-list')

    species_href_list: list = []
    subspecies_href_list: list = []

    if main_list:
        li_elements_list = main_list.find_all('li')
        for li_element in li_elements_list:
            # li_id_name = li_element.get('id')
            # 往下寻找tax-tree标签
            # tax_tree_element = soup.select_one('tax-breadcrumb.tax-tree')
            # 查找 <a> 元素
            # a_element = li_element.find('a', class_='tax-breadcrumb.tax-tree.last-child')
            a_element = li_element.find('a', class_='last-child color-species')
            # 检查是否找到 <a> 元素
            if a_element:
                # 获取 <a> 元素的 href 属性
                href = a_element.get('href')
                href = urljoin(new_base_url, href)
                species_href_list.append(href)
                # print(href)
            else:
                subspecies_a_element = li_element.find('a', class_='color-subspecies')
                if subspecies_a_element is None:
                    # print(li_element)
                    continue
                href = subspecies_a_element.get('href')
                subspecies_href_list.append(href)

    return species_href_list, subspecies_href_list

def fetch_species_href_fromA2z(url: str):
    # 调用上面定义的函数，获取物种名称列表
    url, params_list = generate_url_with_page(url)
    all_species_href_list = []
    all_subspecies_href_list = []
    for params in tqdm(params_list, desc='Fetching Species', unit='rounds'):
        species_href_list, subspecies_href_list = fetch_species_href(url=url, params=params)
        all_species_href_list.extend(species_href_list)
        all_subspecies_href_list.extend(subspecies_href_list)
    
    print(f"The Number of Total Species Elements is: {len(all_species_href_list)}")
    print(f"The Number of Total Sub Species Elements is: {len(all_subspecies_href_list)}")

    return all_species_href_list, all_subspecies_href_list

def fetch_specie_16S_rRNA_sequence(url: str):
    # url = https://lpsn.dsmz.de/species/abditibacterium-utsteinense
    sepecie_soup = soup_extract(url=url)

    # 提取URL的最后一部分
    specie_name = url.split('/')[-1]

    # 检查是否存在连字符
    if '-' in specie_name:
        # 将连字符替换为空格
        specie_name = specie_name.replace('-', ' ')

    # 将整个字符串的首个字母变为大写
    specie_name = specie_name.capitalize()

    # print(specie_name)  # 输出: Aadella gelida

    # base_url = “https://lpsn.dsmz.de/species”
    base_url = generate_base_url(url=url)

    fasta_a_element = sepecie_soup.find('a', class_='fasta-download')

    if fasta_a_element:
        href = fasta_a_element.get('href') 
        fasta_a_download_url = urljoin(base_url, href)
        response = requests.get(fasta_a_download_url)
        if response.status_code == 200:
            # # 找到class为"title color-species"的<h1>标签
            # title_tag = sepecie_soup.find('h1', class_='title color-species') 

            # # 获取标签内的所有文本，包括<i>标签内的文本
            # text_content = title_tag.get_text() if title_tag else ""

            
            content = response.text
            lines = content.split('\n', 1)
            sequence_name: str = lines[0]
            rna_sequence: str = lines[1]
            # print(lines[1])

            # print(content)

            return {'specie_name': specie_name, 'sequence_name': sequence_name, 'url': url,'rna_sequence': rna_sequence}


        else:
            print("Failed to retrieve the content, status code:", response.status_code)
    
    return None

# def fetch_specie_16S_rRNA_sequence_multi_urls(url: str):
    


# 确保只有在直接运行这个脚本时才执行下面的代码
if __name__ == "__main__":
    all_species_href_list, all_subspecies_href_list = fetch_species_href_fromA2z(SPECIES_URL)
    # base_url = “https://lpsn.dsmz.de/species”
    # base_url = generate_base_url(url="https://lpsn.dsmz.de/species/abditibacterium-utsteinense")

    species_names = []
    sequence_names = []
    url_list = []
    rna_sequence_list = []
    

    unable_download_species_href_list = []

    # for species_href in all_species_href_list:
    for species_href in tqdm(all_species_href_list, desc='Processing species', unit='species'):
        # rna_sequence_dict = {'specie_name': specie_name, 'sequence_name': sequence_name, 'url': url,'rna_sequence': rna_sequence}
        rna_sequence_dict = fetch_specie_16S_rRNA_sequence(url=species_href)
        if rna_sequence_dict:
            species_names.append(rna_sequence_dict['specie_name'])
            sequence_names.append(rna_sequence_dict['sequence_name'])
            url_list.append(rna_sequence_dict['url'])
            rna_sequence_list.append(rna_sequence_dict['rna_sequence'])
        else:
            unable_download_species_href_list.append(species_href)

    
    print(f"The Total Number of Downloaded Species Elements is: {len(all_species_href_list)}")
    print(f"The Number of Species Elements unable to download is: {len(unable_download_species_href_list)}")

    data = {'specie_name': species_names, 'sequence_name': sequence_names, 'url': url_list,'rna_sequence': rna_sequence_list}

    # 创建DataFrame
    df = pd.DataFrame(data)

    # 保存到Excel文件
    df.to_excel("output.xlsx", index=False, engine='openpyxl')



    # fetch_specie_16S_rRNA_sequence(url="https://lpsn.dsmz.de/species/abditibacterium-utsteinense")

    

# <li>
# <a class="color-subspecies" href="/subspecies/azotobacter-chroococcum-isscasi">
# <strong>
# <i>Azotobacter</i> 
# <i>chroococcum</i> subsp. 
# <i>isscasi</i>
# </strong>
# </a> 
# </li>
