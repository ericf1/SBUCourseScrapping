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

all_course_types = ["CSE"]


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
            partially = single_course_name.find_all(
                "span", {"class": "partial-message"})
            partially_fulfilled_list = None
            if partially:
                for partially_fulfilled in partially:
                    partially_fulfilled_list = [partially_fulfilled_content.contents[0]
                                                for partially_fulfilled_content in partially_fulfilled.find_all("a")]
                    partially = f'Partially Fulfilled: {" ".join(partially_fulfilled_list)}'

            if SBCs:
                all_SBCs = [SBC.contents[0] for SBC in SBCs]
                if partially_fulfilled_list is not None:
                    all_SBCs = set(all_SBCs).symmetric_difference(
                        set(partially_fulfilled_list))
                    all_SBCs = list(all_SBCs)
                    all_SBCs.append(partially)

                all_SBCs = " ".join(all_SBCs)
            else:
                all_SBCs = ""
            combined_reqs = {}

            req_checks = single_course_name.find_all("p")
            all_reqs = [
                req_check.contents[0] for req_check in req_checks if req_check.contents and "requisite" in req_check.contents[0]]
            if all_reqs:
                all_reqs_array = all_reqs[0].split(": ")
                combined_reqs[all_reqs_array[0]] = [all_reqs_array[1].lstrip()]

            for req_check in req_checks:
                req_check_with_i = req_check.find("i")
                if req_check_with_i:
                    combined_reqs[req_check_with_i.contents[0]
                                  [:-1]] = [req_check_with_i.lstrip() for req_check_with_i in req_check_with_i.parent.contents[2][1:-4:].lstrip().split("; ")]

            formatted_all_reqs = {}
            for key, value in combined_reqs.items():
                if "or " in key and "Advisory" in key:
                    formatted_all_reqs["Advisory Prerequisite or Corequisite"] = "; ".join(
                        value)
                elif "or " in key:
                    formatted_all_reqs["Prerequisite or Corequisite"] = "; ".join(
                        value)
                elif "Advisory" in key:
                    formatted_all_reqs["Advisory Prerequisite"] = "; ".join(
                        value)
                elif "Corequisite" in key or "corequisite" in key:
                    formatted_all_reqs["Corequisite"] = "; ".join(
                        value)
                elif "requisite" in key or "Requisite" in key:
                    formatted_all_reqs["Prerequisite"] = "; ".join(
                        value)
                else:
                    print(f"{key}: {value} ERROR :^)")
            # print(combined_reqs)
            data = {'Course #': f"{department} {course_number}", 'Dep': department, 'ID': course_number,
                    'Course Name': course_name_condensed, 'SBC': all_SBCs, 'Credits': credit}
            data.update(formatted_all_reqs)
            allData.append(data)
df = pd.DataFrame(allData, columns=['Course #', 'Dep', 'ID', 'Course Name', 'SBC',
                  'Credits', 'Prerequisite', 'Corequisite', 'Advisory Prerequisite', 'Advisory Prerequisite or Corequisite'])
df.to_excel('BetterSBU.xlsx', engine='xlsxwriter', index=False)
# df.to_csv('SBU.csv', sep='\t', encoding='utf-8', index=False)
