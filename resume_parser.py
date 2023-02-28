import re
from copy import deepcopy
from itertools import accumulate
from pprint import pprint
from typing import Optional, Tuple, Union

import pdfplumber as pb
from constants import (  # pylint: disable=[E0402]
    CERT_DIC,
    CITIES,
    CONST_OUTPUT,
    EDU_DIC,
    EDUCATION,
    EXP_DIC,
    EXP_TITLES,
    ISSUERS,
    POSSIBLE_HEADERS,
    PROJ_DIC,
    SKILL_LIST,
)
from helpers.validate_keys import ValidateKeys
from unidecode import unidecode

validate = ValidateKeys()


# ____________________________________________________________ parse P1 ________________________________________________


def check_valid_line(line: str) -> bool:
    """this"""
    if not re.match(r"^[_\W]+$", line):  # pylint:disable=[R1703,R1705]
        return True
    else:
        return False


def pdf_to_words(pdf_file: str) -> list:
    """This"""
    word_details = []
    with pb.open(pdf_file) as pdf:
        pages = pdf.pages
        for page in pages:
            lst_of_words = page.extract_words(
                x_tolerance=1,
                y_tolerance=1,
                extra_attrs=[
                    "page_number",
                    "stroking_color",
                    "non_stroking_color",
                    "size",
                    "fontname",
                ],
            )
            word_details.append(lst_of_words)
    return word_details


def get_line_details(word_details: list) -> list:
    """THis"""
    check_x1, check_top, check_fontname = 0, "", ""
    detailed_lines = []
    x0, top, page_no = 0, 0, 1
    string = ""


    for page in word_details:
        for word in page:
            # adding first word details in the variables
            if check_x1 == 0:
                x0 = word["x0"]
                top = word["top"]
                string = unidecode(word["text"]) + " "
                fontname = word["fontname"]
                stroking_clr = word["stroking_color"]
                non_stroking_clr = word["non_stroking_color"]
                size = word["size"]
            # checking if distance from top is same, gap in
            # between less than 10 as well as fontname is same
            # or not for two words if yes add to line
            elif (
                int(float(word["top"])) == check_top and abs(word["x0"] - check_x1) < 10
            ) and check_fontname == word["fontname"]:
                if abs(word["x0"] - check_x1) < 1:
                    string = string + unidecode(word["text"])
                    string = string.replace(" ", "")
                    string = string + " "
                else:
                    string = string + unidecode(word["text"]) + " "
            # if checks are not matching appends the line in
            # detailed_lines after appending previous line update
            # variables with current details
            else:
                line = {
                    "line": string.rstrip(": "),
                    "x0": x0,
                    "top": top,
                    "page_number": page_no,
                    "fontname": fontname,
                    "stroking_color": stroking_clr,
                    "non_stroking_color": non_stroking_clr,
                    "size": size,
                }
                if check_valid_line(line["line"]):
                    if line["line"]:
                        detailed_lines.append(line)
                page_no = word["page_number"]
                fontname = word["fontname"]
                stroking_clr = word["stroking_color"]
                non_stroking_clr = word["non_stroking_color"]
                size = word["size"]
                x0 = word["x0"]
                top = word["top"]
                string = unidecode(word["text"]) + " "
            # update checks in each iterations
            check_top = int(float(word["top"]))  # type: ignore
            check_x1 = word["x1"]
            check_fontname = word["fontname"]
    if len(detailed_lines) == 0:
        return []
    if "curriculum vit" in detailed_lines[0]["line"].lower():
        detailed_lines.pop(0)
    return detailed_lines


def get_p1(pdf_file: str) -> list:
    """Calls"""
    word_details = pdf_to_words(pdf_file)
    details = get_line_details(word_details)
    return details


# ____________________________________________________________ parse P2 ________________________________________________


def is_near(
    num1: Union[int, float],
    num2: Union[int, float],
    dec: int = 10,
) -> bool:
    """It"""
    if int(abs((num1 - num2) * dec)) == 0:  # pylint: disable=[R1703,R1705]
        return True
    else:
        return False


def find_headers(lines_and_info: list) -> tuple:
    """Thus we will match the size and form our headers list."""
    heads_list = []
    size_list = []
    for i, ele in enumerate(lines_and_info):  # pylint: disable=[W0612]
        if lines_and_info[i]["line"].lower() in POSSIBLE_HEADERS:
            heads_list.append(lines_and_info[i])
            size_list.append(lines_and_info[i]["size"])
    counter = 0
    if heads_list:  # pylint: disable=[R1705]
        size = size_list[0]
        for num in size_list:
            curr_frequency = size_list.count(size)
            if curr_frequency > counter:
                counter = curr_frequency
                size = num
        header_detail = []
        header_text = []
        for head in heads_list:
            if is_near(head["size"], size):
                header_detail.append(head)
                header_text.append(head["line"])
        header_info = {
            "fontname": header_detail[0]["fontname"],
            "size": header_detail[0]["size"],
        }

        return header_detail, header_text, header_info
    else:
        return None, None, None


def check_column(headers: list) -> Union[list, None]:
    """this"""
    page1_dic = []
    for cont in headers:
        if cont["page_number"] == 1:
            page1_dic.append(cont)
    for n, item in enumerate(page1_dic):  # pylint: disable=[W0612]
        if n == (len(page1_dic) - 1):
            break
        if abs(page1_dic[n + 1]["x0"] - page1_dic[n]["x0"]) > 60:
            return [
                max(item["x0"] for item in page1_dic),
                min(item["top"] for item in page1_dic),
            ]
    return None


def merge_para(result_with_info: list) -> list:
    """Takes"""
    merged_lines = []
    line = {}
    for itr, each_line in enumerate(result_with_info):
        if "(cid:" not in each_line["line"]:
            if itr == 0:
                line = each_line
            elif each_line["top"] == result_with_info[itr - 1]["top"]:
                merged_lines.append(line)
                line = each_line
            elif (
                each_line["fontname"] == result_with_info[itr - 1]["fontname"]
                and is_near(
                    each_line["size"],
                    result_with_info[itr - 1]["size"],
                    100,
                )
                and result_with_info[itr - 1]["non_stroking_color"]
                == each_line["non_stroking_color"]
                and each_line["top"] - result_with_info[itr - 1]["top"]
                <= (each_line["size"] * 1.53)
            ):
                line["line"] = line["line"] + " " + "\n" + " " + each_line["line"]
            else:
                merged_lines.append(line)
                line = each_line
    merged_lines.append(line)
    return merged_lines


def split_sides(lines_and_info: list, partition_info: list) -> list:
    """this"""
    top = []
    left = []
    right = []

    for n, ele in enumerate(lines_and_info):  # pylint: disable=[W0612]
        if (
            lines_and_info[n]["top"] < (partition_info[1] - 5)
            and lines_and_info[n]["page_number"] == 1
        ):
            top.append(lines_and_info[n])

        if (
            lines_and_info[n]["x0"] > (partition_info[0] - 10)
            and lines_and_info[n]["page_number"] == 2
        ):
            right.append(lines_and_info[n])

        if (
            lines_and_info[n]["x0"] < (partition_info[0] - 10)
            and lines_and_info[n]["page_number"] == 2
        ):
            left.append(lines_and_info[n])

        if (
            lines_and_info[n]["x0"] > (partition_info[0] - 10)
            and lines_and_info[n]["top"] > (partition_info[1] - 5)
            and lines_and_info[n]["page_number"] == 1
        ):
            right.append(lines_and_info[n])

        elif (
            lines_and_info[n]["x0"] < (partition_info[0] - 10)
            and lines_and_info[n]["top"] > (partition_info[1] - 5)
            and lines_and_info[n]["page_number"] == 1
        ):
            left.append(lines_and_info[n])

    final_list = top + left + right

    return final_list


def seprate_sections(list_of_lines: list, headers: list, header_details: dict) -> list:
    """this"""
    size_lst = []
    for each_line in list_of_lines:
        if each_line["line"].lower() not in POSSIBLE_HEADERS:
            size_lst.append(each_line["size"])
    max_size = max(size_lst)
    section: list = []
    for i, itr in enumerate(list_of_lines):
        temp = []
        if itr["size"] == max_size:
            temp.append(itr)
            for itr2 in list_of_lines[i + 1 :]:  # noqa: E203
                if itr2["line"] in headers:  # pylint: disable=[R1723]
                    break
                elif itr2["fontname"] == header_details["fontname"] and is_near(
                    itr2["size"], header_details["size"]
                ):
                    break
                else:
                    temp.append(itr2)
            section = [temp] + section
        elif (
            itr["fontname"] == header_details["fontname"]
            and is_near(itr["size"], header_details["size"])
        ) or itr["line"].lower() in POSSIBLE_HEADERS:
            temp.append(itr)
            for itr2 in list_of_lines[i + 1 :]:  # noqa: E203
                if itr2["fontname"] == header_details[  # pylint: disable=[R1723]
                    "fontname"
                ] and is_near(itr2["size"], header_details["size"]):
                    break
                elif itr2["line"] in headers:
                    break
                else:
                    temp.append(itr2)
            section.append(temp)
    return section


def post_processing(sect_list: list) -> dict:
    """this"""
    section = []
    for j, sec in enumerate(sect_list):
        if isinstance(sec, type(dict)):
            continue
        if j == 0:
            content = []
            for i, itr in enumerate(sec):
                if i == 0:
                    name = sec[0]["line"]
                elif sec[0]["size"] == itr["size"]:
                    name = name + " " + itr["line"]
                else:
                    content.append(sec[i])
                dic = {}
                dic[name] = content
            section.append(dic)
        else:
            for i, itr in enumerate(sec):
                dic = {}
                if i == 0:
                    dic[sec[0]["line"]] = sec[1:]
                    section.append(dic)
                else:
                    break
    section_detail = {}
    for index, sec in enumerate(section):
        for key, lst in sec.items():
            if index == 0:
                section_detail[key] = lst
            elif key.lower() in POSSIBLE_HEADERS:
                section_detail[key] = lst
            else:
                if "others" in section_detail:
                    section_detail["others"].append(sec)
                else:
                    section_detail["others"] = []
                    section_detail["others"].append(sec)
    return section_detail


def get_lines_only(section_detail):
    """It return lines only for each section."""
    result: dict = {}
    for head, item in section_detail.items():
        if head == "others":
            result[head] = {}
            for each_unknown in item:
                result[head][list(each_unknown.keys())[0]] = []
                for line in each_unknown[list(each_unknown.keys())[0]]:
                    if isinstance(line, dict):
                        result[head][list(each_unknown.keys())[0]].append(line["line"])
        else:
            result[head] = []
            for line in item:
                result[head].append(line["line"])
    return result


def get_p2(p1_res: list) -> Tuple[Optional[dict], Optional[dict]]:
    """this"""
    headers = find_headers(p1_res)
    if headers[0]:
        column_present = check_column(headers[0])
    else:
        return None, None

    if column_present:
        list_of_lines = split_sides(p1_res, column_present)
    else:
        list_of_lines = p1_res

    merged_lines = merge_para(list_of_lines)

    sec = seprate_sections(merged_lines, headers[1], headers[2])
    detail_res = post_processing(sec)
    result = get_lines_only(detail_res)

    return result, detail_res


# ____________________________________________________________ parse P3 _________________________________________________


def remove_newline(line: str) -> str:
    """Remove \n from the given line"""
    return line.replace("\n ", "")


def extract_date_p3(line: str) -> list:
    """It"""
    rgx = re.compile(
        r"^(([0-9]|0[1-9]|10|11|12)/((20|19)[0-9]{2}|([0-9]{2})))|(20|19)[0-9]{2}|(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|jun(e)?|jul(y)?|aug(ust)?|sep(tember)?|sept(ember)?|oct(ober)?|nov(ember)?|dec(ember)?)(\s|-|.\s|\s-\s|-\s|\s-|')+\d{1,4}|present|ongoing",  # noqa
        re.I,
    )
    split_line = re.split(r"to|-\s|-|\s-|\s-\s|\s", line)
    years = []
    for ele in split_line:
        match = rgx.match(ele)
        if match:
            years.append(match.group())
    return years


def div_datewise(content: list) -> list:
    """Based"""
    found = False
    count = 0
    length_to_split = []
    pos = []
    for index, each in enumerate(content):
        count += 1
        match = extract_date_p3(each)
        if match:
            if found is False:
                found = True
                match_ct = count
                continue
            pos.append(index + 1 - match_ct)
    pos.append(len(content))
    length_to_split.append(pos[0])
    length_to_split.extend([y - x for x, y in zip(pos, pos[1:])])
    if length_to_split:  # pylint:disable=[R1705]
        div = [
            content[x - y : x]  # noqa: E203
            for x, y in zip(
                accumulate(length_to_split),
                length_to_split,
            )
        ]
        return div
    else:
        return content


def div_sizewise(result_det: list) -> list:
    """Takes"""
    size_list = []
    if len(result_det) == 0:
        return []
    for i, ele in enumerate(result_det):  # pylint: disable=[W0612]
        size_list.append(ele["size"])
    max_size = max(size_list)
    for item in result_det:
        if item["size"] == max_size:
            ele_color = item["non_stroking_color"]
            break
    div = []
    line: list = []
    # Comparing each element with first item
    for i, item in enumerate(result_det):
        if (
            is_near(max_size, item["size"])
            and ele_color == item["non_stroking_color"]
            and item["top"] - result_det[i - 1]["top"] >= (item["size"] * 1.51)
        ):
            div.append(line)
            line = [item["line"]]
        else:
            line.append(item["line"])
    div.append(line)
    return div


def check_n_div_content(list_of_lines: list, list_of_lines_w_det: list) -> list:
    """It"""
    chk: Union[list, bool] = False
    for line in list_of_lines:
        chk = extract_date_p3(line)
        if chk:
            break
    if chk:
        res = div_datewise(list_of_lines)
    else:
        res = div_sizewise(list_of_lines_w_det)
    return res


def extract_edu(result: dict, result_w_det: dict, output: dict) -> dict:
    """This"""
    city = re.compile("|".join(re.escape(x.lower()) for x in CITIES))
    educ = re.compile("|".join(re.escape(x.lower()) for x in EDUCATION))
    for edu in result:  # pylint:disable=[R1702]
        if "educ" in edu.lower() or "acad" in edu.lower() and "proj" not in edu.lower():
            ed_lst = check_n_div_content(result[edu], result_w_det[edu])
            for each_lst in ed_lst:
                edu_dic = deepcopy(EDU_DIC)
                for info in each_lst:
                    info = remove_newline(info)
                    marks = re.findall(
                        r"\d+\.\d+|\d+\%|cgpa|percent|grade|gpa",
                        info.lower(),
                    )
                    match = re.search(educ, info.lower())
                    years = extract_date_p3(info)
                    location = re.findall(city, info.lower())
                    flag = 0
                    if match:
                        if not edu_dic["degree"]:
                            edu_dic["degree"] = info
                            flag = 1
                    if years:
                        edu_dic["endDate"] = info
                        flag = 1
                    if marks:
                        edu_dic["cgpa"] = info
                        flag = 1
                    if location:
                        edu_dic["location"] = info
                    if not flag:
                        edu_dic["school"] = edu_dic["school"] + info + " "
                output["education"].append(edu_dic)
            break
    return output


def extract_exp(result: dict, result_w_det: dict, output: dict) -> dict:
    """Extracts"""
    title_reg = re.compile("|".join(re.escape(x) for x in EXP_TITLES))
    city_reg = re.compile("|".join(re.escape(x.lower()) for x in CITIES))
    exp_list = []
    for exp in result:  # pylint:disable=[R1702]
        if (
            "exper" in exp.lower()
            or "intern" in exp.lower()
            or "training" in exp.lower()
        ):
            exp_lst = check_n_div_content(result[exp], result_w_det[exp])
            for each_lst in exp_lst:
                exp_dic = deepcopy(EXP_DIC)
                for line in each_lst:
                    line = remove_newline(line)
                    title = re.findall(title_reg, line.lower())
                    if title:
                        if not exp_dic["title"] and len(title) < 50:
                            exp_dic["title"] = line
                            continue
                    years = extract_date_p3(line)
                    if years:
                        if not exp_dic["endDate"]:
                            exp_dic["endDate"] = line
                            continue
                    location = re.findall(city_reg, line.lower())
                    if not exp_dic["location"]:
                        if location:
                            exp_dic["location"] = line
                            continue
                    if not exp_dic["company"] and len(line) < 50:
                        exp_dic["company"] = line
                    exp_dic["description"] = exp_dic["description"] + line + " "
                exp_list.append(exp_dic)
            output["experiences"] = exp_list
            break
    return output


def extract_publication(result_w_det: dict, output: dict) -> dict:
    """Extract"""
    for pub in result_w_det:
        if "publ" in pub.lower() or "research" in pub.lower():
            pub_list = div_sizewise(result_w_det[pub])
            for each_pub in pub_list:
                desc = " "
                output["publications"].append(desc.join(each_pub))
            break
    return output


def extract_volun(result_w_det: dict, output: dict) -> dict:
    """Extract"""
    for volun in result_w_det:
        if "volun" in volun.lower() or "community" in volun.lower():
            vol_list = div_sizewise(result_w_det[volun])
            for each_vol in vol_list:
                desc = " "
                output["volunteer_work"].append(desc.join(each_vol))
            break
    return output


def extract_curr(result_w_det: dict, output: dict) -> dict:
    """Extract extra curricular activities done by candidate."""
    output["extra_curricular"] = []
    for cur in result_w_det:
        if "curri" in cur.lower() or "of resp" in cur.lower():
            ext_curr_list = div_sizewise(result_w_det[cur])
            for each_ext_curr in ext_curr_list:
                desc = " "
                output["extra_curricular"].append(desc.join(each_ext_curr))
            break
    return output


def extract_skill(result: dict, output: dict) -> dict:
    """Extract skills listed or present in the resume."""
    for skill in result:
        if skill.lower() in SKILL_LIST:
            if output["skills"]:
                output["skills"] = output["skills"] + result[skill]
            else:
                output["skills"] = result[skill]
    return output


def extract_cert(result: dict, result_w_det: dict, output: dict) -> dict:
    """Extract"""
    issuer = re.compile("|".join(re.escape(x.lower()) for x in ISSUERS))
    res, cert_list = [], []
    for cert in result:
        if "cour" in cert.lower() or "cert" in cert.lower():
            if result[cert]:
                res = check_n_div_content(result[cert], result_w_det[cert])
                break
    if res:
        for each_cert in res:
            cert = deepcopy(CERT_DIC)
            for itr, line in enumerate(each_cert):
                line = remove_newline(line)
                urls = re.findall(
                    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+",
                    line,
                )
                provider = re.search(issuer, line.lower())
                years = extract_date_p3(line)
                flag = 0
                if itr == 0:
                    cert["title"] = line
                    flag = 1
                if years:
                    cert["description"] = line
                    flag = 1
                if urls:
                    cert["certiLink"] = line
                    flag = 1
                if provider:
                    cert["issuer"] = cert["issuer"] + line + " "
                    flag = 1
                if flag == 0:
                    cert["description"] = cert["description"] + line + " \n "
            cert["description"] = cert["description"].rstrip(" \n ")
            cert_list.append(cert)
        output["courses"] = cert_list
    return output


def extract_achiv(result: dict, output: dict) -> dict:
    """Extract"""
    for achi in result:
        if (
            "accompl" in achi.lower()
            or "achiev" in achi.lower()
            or "honor" in achi.lower()
            or "award" in achi.lower()
        ):
            output["achievement"] = result[achi]
            break
    return output


def extract_proj(result: dict, result_w_det: dict, output: dict) -> dict:
    """Extract project details done by the candidate."""
    proj_list, res = [], []
    for proj in result:
        if "proj" in proj.lower():
            if result[proj]:
                res = check_n_div_content(result[proj], result_w_det[proj])
                break
    for each_proj in res:
        proj = deepcopy(PROJ_DIC)
        for itr, line in enumerate(each_proj):
            line = remove_newline(line)
            years = extract_date_p3(line)
            flag = 0
            if itr == 0:
                proj["name"] = line
                flag = 1
            if years:
                proj["endDate"] = line
                flag = 1
            if flag == 0:
                proj["description"] = proj["description"] + line + " "
        proj_list.append(proj)
    output["projects"] = proj_list
    return output


def extract_about(result: dict, output: dict) -> dict:
    """Extract"""
    for about in result:
        output["name"] = about
        line = " "
        line = line.join(result[about])
        line = remove_newline(line)
        output["email"] = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", line)
        output["phone_number"] = re.findall(r"\+?[136789][\d -]{8,13}\d", line)
        break
    for about in result:
        if "personal info" in about.lower() or "personal detail" in about.lower():
            line = " "
            line = line.join(result[about])
            line = remove_newline(line)
            email = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", line)
            if email:
                output["email"] = email
            ph_no = re.findall(r"\+?[136789][\d -]{8,13}\d", line)
            if ph_no:
                output["phone_number"] = ph_no
            break
    if "others" in result.keys():
        keys = list(result["others"].keys())
        for each_key in keys:
            if "contact" in each_key.lower():
                line = " "
                line = line.join(result["others"][each_key])
                line = remove_newline(line)
                email = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", line)
                if email:
                    output["email"] = email
                ph_no = re.findall(r"\+?[136789][\d -]{8,13}\d", line)
                if ph_no:
                    output["phone_number"] = ph_no
            if "address" in each_key.lower():
                output["location"] = result["others"][each_key]
    return output


def get_p3(p2_res: dict, p2_res_det: dict) -> dict:
    """This"""
    output = deepcopy(CONST_OUTPUT)
    extract_edu(p2_res, p2_res_det, output)
    extract_about(p2_res, output)
    extract_exp(p2_res, p2_res_det, output)
    extract_publication(p2_res_det, output)
    extract_volun(p2_res_det, output)
    extract_skill(p2_res, output)
    extract_cert(p2_res, p2_res_det, output)
    extract_achiv(p2_res, output)
    extract_proj(p2_res, p2_res_det, output)
    extract_curr(p2_res_det, output)

    return output


# ____________________________________________________ parse P4 __________________________________________________________________


def extract_date_p4(line: str) -> list:
    """This"""
    rgx = re.compile(
        r"^(([0-9]|0[1-9]|10|11|12)/((20|19)[0-9]{2}|([0-9]{2})))|(20|19)[0-9]{2}|(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|jun(e)?|jul(y)?|aug(ust)?|sep(tember)?|sept(ember)?|oct(ober)?|nov(ember)?|dec(ember)?)(\s|-|.\s|\s-\s|-\s|\s-|')+\d{1,4}|present|ongoing",  # noqa
        re.I,
    )  # noqa
    split_line = re.split(r"to|-\s|-|\s-|\s-\s|\s", line)
    years = []
    for ele in split_line:
        match = rgx.match(ele)
        if match:
            years.append(match.group())
    return years


def list_to_str(res: list) -> str:
    """This"""
    string = ","
    result = string.join(res)
    return result


def finalize_ed(res: list) -> list:
    """extract"""
    city = re.compile("|".join(re.escape(x.lower()) for x in CITIES))
    edu_list = []
    for itr, each_deg in enumerate(res):
        edu = deepcopy(EDU_DIC)
        edu["ID"] = itr
        if each_deg["degree"]:
            edu["degree"] = each_deg["degree"]
        if each_deg["endDate"]:
            years = extract_date_p4(each_deg["endDate"])
            if len(years) == 1:
                edu["endDate"] = years[0]
            if len(years) == 2:
                edu["startDate"] = years[0]
                edu["endDate"] = years[1]
        if each_deg["location"]:
            edu["location"] = re.findall(city, each_deg["location"].lower())[0]
        if each_deg["cgpa"]:
            cgpa = re.findall(r"\d+\.\d+|\d+\%|\s%", each_deg["cgpa"])
            if cgpa:
                edu["cgpa"] = cgpa[0]
        edu["school"] = each_deg["school"]
        edu_list.append(edu)
    return edu_list


def finalize_exp(res: list) -> list:
    """extract"""
    city = re.compile("|".join(re.escape(x.lower()) for x in CITIES))
    exp_list = []
    for each_exp in res:
        exp = deepcopy(EXP_DIC)
        if each_exp["title"]:
            exp["title"] = each_exp["title"]
        if each_exp["company"]:
            exp["company"] = each_exp["company"]
        if each_exp["endDate"]:
            years = extract_date_p4(each_exp["endDate"])
            if len(years) == 1:
                exp["endDate"] = years[0]
            if len(years) == 2:
                exp["startDate"] = years[0]
                exp["endDate"] = years[1]
        if each_exp["location"]:
            exp["location"] = re.findall(city, each_exp["location"].lower())[0]
        if each_exp["description"]:
            exp["description"] = each_exp["description"]
        exp_list.append(exp)
    return exp_list


def finalize_proj(res: list) -> list:
    """extract"""
    proj_list = []
    for each_proj in res:
        proj = deepcopy(PROJ_DIC)
        if each_proj["name"]:
            proj["name"] = each_proj["name"]
        if each_proj["endDate"]:
            years = extract_date_p4(each_proj["endDate"])
            if len(years) == 1:
                proj["endDate"] = years[0]
            if len(years) == 2:
                proj["startDate"] = years[0]
                proj["endDate"] = years[1]
        if each_proj["description"]:
            proj["description"] = each_proj["description"]
        proj_list.append(proj)
    return proj_list


def finalize_skills(res: list) -> list:
    """we are checking"""
    skills = []
    for line in res:
        matches = re.split(r",\s|,|-\s|and\s", line)
        if matches:
            res = list(filter(None, matches))
            skills.extend(res)
    skills = list(set(skills))
    return skills


def finalize_course(res: list) -> list:
    """finalizes course and its provider."""
    cour_list = []
    issuer = re.compile("|".join(re.escape(x.lower()) for x in ISSUERS))
    for each_course in res:
        cour = deepcopy(CERT_DIC)
        if each_course["title"]:
            cour["title"] = each_course["title"]
        if each_course["description"]:
            cour["description"] = each_course["description"]
        if each_course["issuer"]:
            provider = re.search(issuer, each_course["issuer"].lower())
            if provider:
                cour["issuer"] = provider.group()
        if each_course["certiLink"]:
            cour["certiLink"] = each_course["certiLink"]
        cour_list.append(cour)
    return cour_list


def finalize_ext_curr(res: list, exp_list: list) -> list:
    """Move extra curricular to experience."""
    for each_ext_curr in res:
        exp = deepcopy(EXP_DIC)
        exp["description"] = each_ext_curr
        exp_list.append(exp)
    return exp_list


def get_p4(p3_res: dict) -> Optional[dict]:
    """extract the exact information from the lines"""
    output = deepcopy(CONST_OUTPUT)
    if p3_res["name"]:
        output["name"] = p3_res["name"]
    phone = list_to_str(p3_res["phone_number"])
    if phone:
        output["phone_number"] = phone
    email = list_to_str(p3_res["email"])
    if email:
        output["email"] = email
    if p3_res["education"]:
        edu = finalize_ed(p3_res["education"])
        output["education"] = edu
    if p3_res["experiences"]:
        exp = finalize_exp(p3_res["experiences"])
        output["experiences"] = exp
    if p3_res["skills"]:
        skills = finalize_skills(p3_res["skills"])
        output["skills"] = skills
    if p3_res["volunteer_work"]:
        output["volunteer_work"] = p3_res["volunteer_work"]
    if p3_res["projects"]:
        projects = finalize_proj(p3_res["projects"])
        output["projects"] = projects
    if p3_res["courses"]:
        course = finalize_course(p3_res["courses"])
        output["courses"] = course
    if p3_res["extra_curricular"]:
        exp = finalize_ext_curr(p3_res["extra_curricular"], output["experiences"])
        output["experiences"] = exp
    if p3_res["publications"]:
        pub = p3_res["publications"]
        output["publications"] = pub
    if p3_res["achievement"]:
        output["achievement"] = p3_res["achievement"]
    errors = validate.validate_result(output)
    if errors:  # pylint: disable=[R1705]
        print(errors)
        return None
    else:
        return output


# __________________________________________________________________________________________________________________________________


def process_request(  # pylint: disable=[R0022]
    pdf_file: str, response: dict, table: str, keys_: dict
) -> Optional[dict]:
    """this"""
    response["type_"] = "general"
    response["parse_status"] = []
    result: dict = {
        "p1": [],
        "p2": {},
        "p3": {},
        "p4": {},
    }
    result["p1"] = get_p1(pdf_file)
    if result["p1"]:
        response["full_output"] = result

        result["p2"], p2_res_det = get_p2(result["p1"])
        if result["p2"]:
            response["full_output"] = result
            response["parse_status"].append("p1_complete")
            response["parse_status"].append("p2_complete")

            # print(result["p2"])

            result["p3"] = get_p3(result["p2"], p2_res_det)
            if result["p3"]:
                response["full_output"] = result
                response["parse_status"].append("p3_complete")

                result["p4"] = get_p4(result["p3"])
                if result["p4"]:  # pylint: disable=[R1705]
                    response["full_output"] = result
                    response["parse_status"].append("p4_complete")
                    response["full_is_parsed"] = True

                    pprint(result["p4"])
                    return response

                else:
                    print("p4 parser failed.")
                    return None
            else:
                print("p3 parser failed.")
                return None
        else:
            print("p2 parser failed.")
            return None
    else:
        print("p1 parser failed")
        return None


# _______________________________________________________________________________________________________________________________________


file1 = "./637a1cc51da81cde8ff5e177_1677548487.751984.pdf"  # perfect case

file2 = "./5fcde140dcd1797990d5adcb_1671966868.6323903.pdf" # max() error
file2_1 ="./632dab49259836002f29d7b5_1672398248.2854657.pdf"
file3 = "./63fc2daa95f87ac5f6a7808a_1677471183.4823444.pdf" # not a PDF Error
file4 = "./6339c9a9aa77440104de9f64_1664731767.8778086.pdf" # list index out of range
file4_1 = "./6325cfae9037d30030485d20_1663425644.55769.pdf" #     ""
file_5 = "./5f3b686472cebb6673435395_1618294181.0.pdf"      # not enough values to unpack
file_6 = "./5f4353814fc740311f7543c1_1618294176.0.pdf"      # string indices must be int

pdf_file = file_6
response = {}
table = "some"
keys_ = "some"
process_request(pdf_file, response, table, keys_)
