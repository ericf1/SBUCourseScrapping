import requests
import unicodedata
from bs4 import BeautifulSoup
import concurrent.futures
import pandas as pd

r = requests.get(
    'https://www.stonybrook.edu/sb/bulletin/current/courses/browse/byabbreviation/')

soup = BeautifulSoup(r.content, "html.parser")

results = soup.find(id="bulletin_course_search_table")

children = results.find_all('a')[::2]

all_course_types = [child.contents[0] for child in children]

# all_course_types = [all_course_types[0], all_course_types[1]]


def get_info_from_course_type(course_type):
    r = requests.get(
        f'https://www.stonybrook.edu/sb/bulletin/current/courses/{course_type}/')
    return r


allData = []
with concurrent.futures.ThreadPoolExecutor() as executor:
    # print(all_course_types)
    results = executor.map(get_info_from_course_type, all_course_types)

    for r in results:
        soup = BeautifulSoup(r.content, "html.parser")
        course_name = soup.find_all("div", class_="course")
        for single_course_name in course_name:
            unicode_str = single_course_name.find("h3").contents[0]
            course_name_unicode = unicodedata.normalize("NFKD", unicode_str)
            department = course_name_unicode.split()[0]
            course_number = course_name_unicode.split()[1][:-1]
            course_name_condensed = course_name_unicode.split()[2::]
            course_name_condensed = " ".join(course_name_condensed)
            # print(course_number, department, course_name_condensed)

            credit = single_course_name.find_all("p")[-1].contents[0]
            if "-" in credit:
                credit = credit[0:3]
            else:
                credit = credit[0]
            # print(credit)

            SBCs = single_course_name.find_all("a")
            if SBCs:
                SBCs = " ".join([SBC.contents[0] for SBC in SBCs])
            else:
                SBCs = ""
            data = {'Course #': f"{department} {course_number}", 'Dep': department, 'ID': course_number,
                    'Course Name': course_name_condensed, 'SBC': SBCs, 'Credits': credit}
            allData.append(data)
            # print(SBCs)

df = pd.DataFrame(
    allData, columns=['Course #', 'Dep', 'ID', 'Course Name', 'SBC', 'Credits'])
df.to_csv('SBU.csv', sep='\t', encoding='utf-8', index=False)
