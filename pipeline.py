import csv
from dataclasses import dataclass
import types
import typing
import os
from typing import List, Dict
from shutil import rmtree, copy
from os import path, mkdir, system
import requests
import zipfile
import re
import logging
import subprocess

logging.basicConfig(filename='log.log', level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

DATASET_PATH = "MLCQCodeSmellSamples.csv"
DOWNLOAD_PATH = "repos"
RESULTS_PATH = "results"


@dataclass
class Record:
    id: str
    reviewer_id: str
    sample_id: str
    smell: str
    severity: str
    review_timestamp: str
    type: str
    code_name: str
    repository: str
    commit_hash: str
    path: str
    start_line: str
    end_line: str
    link: str
    is_from_industry_relevant_project: str


@dataclass
class ClassMetric:
    file: str
    className: str
    type: str
    cbo: str
    wmc: str
    dit: str
    rfc: str
    lcom: str
    tcc: str
    lcc: str
    totalMethodsQty: str
    staticMethodsQty: str
    publicMethodsQty: str
    privateMethodsQty: str
    protectedMethodsQty: str
    defaultMethodsQty: str
    abstractMethodsQty: str
    finalMethodsQty: str
    synchronizedMethodsQty: str
    totalFieldsQty: str
    staticFieldsQty: str
    publicFieldsQty: str
    privateFieldsQty: str
    protectedFieldsQty: str
    defaultFieldsQty: str
    visibleFieldsQty: str
    finalFieldsQty: str
    synchronizedFieldsQty: str
    nosi: str
    loc: str
    returnQty: str
    loopQty: str
    comparisonsQty: str
    tryCatchQty: str
    parenthesizedExpsQty: str
    stringLiteralsQty: str
    numbersQty: str
    assignmentsQty: str
    mathOperationsQty: str
    variablesQty: str
    maxNestedBlocksQty: str
    anonymousClassesQty: str
    innerClassesQty: str
    lambdasQty: str
    uniqueWordsQty: str
    modifiers: str
    logStatementsQty: str


@dataclass
class MethodMetric:
    file: str
    className: str
    method: str
    constructor: str
    line: str
    cbo: str
    wmc: str
    rfc: str
    loc: str
    returnsQty: str
    variablesQty: str
    parametersQty: str
    methodsInvokedQty: str
    methodsInvokedLocalQty: str
    methodsInvokedIndirectLocalQty: str
    loopQty: str
    comparisonsQty: str
    tryCatchQty: str
    parenthesizedExpsQty: str
    stringLiteralsQty: str
    numbersQty: str
    assignmentsQty: str
    mathOperationsQty: str
    maxNestedBlocksQty: str
    anonymousClassesQty: str
    innerClassesQty: str
    lambdasQty: str
    uniqueWordsQty: str
    modifiers: str
    logStatementsQty: str
    hasJavaDoc: str


def read_csv(path: str) -> List[Record]:
    with open(path) as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        return [Record(*row) for row in reader if row][1:]


def get_repo_name(repository: str, commit_hash: str):
    repo_path = repository[repository.index(
        "github.com:") + 11: repository.index(".git")]
    return repo_path.replace("/", '_')


def download_form_gh(repository: str, commit_hash: str, download_dir: str):
    repo_name = get_repo_name(repository, commit_hash)
    repo_path = repo_name.replace("_", '/')
    r = requests.get(
        f'https://github.com/{repo_path}/archive/{commit_hash}.zip', allow_redirects=True)
    open(path.join(download_dir, f'{repo_name}.zip'), 'wb').write(r.content)


def normalize_code_name(code_name: str) -> str:
    return code_name.replace("$", ".")


METHOD_RE = re.compile('(.*)\/\d+(?:\[(.*)\])?')
GENERIC_RE = re.compile('(.*?)<(.*)>')


def normalize_method_name(method_name: str) -> str:
    match = METHOD_RE.match(method_name)
    if "provideRead" in method_name:
        print("bb")

    if not match:
        logging.info(f"Not matched: {method_name}")
        return method_name

    def parser1(param: str):
        results = []
        curbuffer = ""
        genLevel = 0
        buffer = curbuffer

        for c in param:
            if c == "<":
                genLevel += 1
                if genLevel == 1:
                    curbuffer = buffer
                    buffer = ""
                    continue
            if c == ">":
                genLevel -= 1
                if genLevel == 0:
                    buffer = f"{curbuffer}<{', '.join(parser1(buffer))}>"
                    continue
            if c == "," and genLevel == 0:
                results.append(buffer)
                buffer = ""
                continue
            if c == "." and genLevel == 0:
                buffer = ""
                continue
            buffer += c
        results.append(buffer)
        return results

    def replaceGenericType(param: str) -> str:
        genmatch = GENERIC_RE.match(param)
        if not genmatch:
            raise Exception("YOU FAILED")
        subtype = [replacer(stype) for stype in genmatch.group(2)]
        return f"{replacer(genmatch.group(1))}<{subtype}>"

    def replacer(param: str) -> str:
        isGeneric = "<" in param and ">" in param
        return param.split('.')[-1] if not isGeneric else replaceGenericType(param)

    second_group = ["|".join(parser1(match.group(2)))
                    ] if match.group(2) else []
    return " ".join([match.group(1), *second_group])


def generate_class_metric(path: str) -> Dict[str, ClassMetric]:
    with open(path) as csvfile:
        reader = csv.reader(csvfile)
        return {normalize_code_name(classMetric.className): classMetric for classMetric in [ClassMetric(*row) for row in list(reader)[1:]]}


def generate_method_metric(path: str) -> Dict[str, MethodMetric]:
    with open(path) as csvfile:
        reader = csv.reader(csvfile)

        items = [MethodMetric(*row) for row in list(reader)[1:]]
        return {
            **{normalize_code_name(f'{methodMetric.className}.{normalize_method_name(methodMetric.method)}'): methodMetric for methodMetric in items},
            **{normalize_code_name(f'{methodMetric.className}#{normalize_method_name(methodMetric.method)}'): methodMetric for methodMetric in items}
        }


def save_to_csv(data_list: List[Dict[str, typing.Any]], filepath: str) -> None:
    print(len(data_list), filepath)
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data_list[0].keys())

        writer.writeheader()
        for item in data_list:
            writer.writerow(item)


def main():
    records = read_csv(DATASET_PATH)

    # Generate repos
    repo_map = {
        f'{record.repository}:{record.commit_hash}':
        {'repository': record.repository, 'commit_hash': record.commit_hash} for record in records
    }
    # Clear DOWNLOAD_PATH
    # if path.exists(DOWNLOAD_PATH):
    #     rmtree(DOWNLOAD_PATH)
    # mkdir(DOWNLOAD_PATH)

    # if not path.exists(RESULTS_PATH):
    #     mkdir(RESULTS_PATH)

    repo_sorted_list = sorted(
        list(repo_map.values()), key=lambda x: f'{x["repository"]}:{x["commit_hash"]}')
#
    fukced_up_repos = ['git@github.com:SAP/SapMachine.git', 'git@github.com:apache/camel.git', 'git@github.com:SAP/iot-starterkit.git', 'git@github.com:Shopify/graphql_java_gen.git', 'git@github.com:Tencent/QMUI_Android.git', 'git@github.com:apache/apex-core.git', 'git@github.com:apache/apex-malhar.git', 'git@github.com:apache/aurora.git', 'git@github.com:apache/axis1-java.git', 'git@github.com:apache/axis2-java.git', 'git@github.com:apache/batik.git', 'git@github.com:apache/fop.git', 'git@github.com:apache/incubator-druid.git', 'git@github.com:apache/incubator-dubbo.git', 'git@github.com:apache/incubator-edgent.git', 'git@github.com:apache/incubator-hudi.git', 'git@github.com:apache/incubator-netbeans-html4j.git', 'git@github.com:apache/incubator-omid.git', 'git@github.com:apache/incubator-plc4x.git', 'git@github.com:apache/incubator-rya.git', 'git@github.com:apache/incubator-shardingsphere.git', 'git@github.com:apache/incubator-skywalking.git', 'git@github.com:apache/meecrowave.git', 'git@github.com:apache/ode.git', 'git@github.com:apache/systemml.git', 'git@github.com:apache/uima-ruta.git', 'git@github.com:apache/webservices-xmlschema.git', 'git@github.com:apache/wss4j.git', 'git@github.com:apache/xml-graphics-commons.git', 'git@github.com:eclipse/ceylon.git', 'git@github.com:eclipse/jnosql-diana-driver.git', 'git@github.com:eclipse/m2e-core.git', 'git@github.com:epam/DLab.git', 'git@github.com:facebook/buck.git', 'git@github.com:google/auto.git', 'git@github.com:google/error-prone-javac.git', 'git@github.com:google/j2objc.git', 'git@github.com:reactor/reactor-core.git', 'git@github.com:spring-projects/spring-security.git', 'git@github.com:spring-projects/sts4.git', "git@github.com:apache/hadoop.git"
                       ]
    # 'git@github.com:yandex/graphouse.git'  # name
    last_repo = ""
    last_repo_idx = [x["repository"]
                     for x in repo_sorted_list].index(last_repo) if last_repo else 0
    sub_repo_sorted_list = repo_sorted_list[last_repo_idx:]

    # Merge results with dataset
    # FIXME FIXME FIXME
    excluded_repos = []
    subset_records = [
        record for record in records if record.repository not in excluded_repos]

    class_records = [
        record for record in subset_records if record.type == "class"]
    method_records = [
        record for record in subset_records if record.type == "function"]

    class_results = []
    method_results = []

    class_records_mapping = dict()
    print(len(class_records))
    for class_record in class_records:
        int_dict_key = f'{class_record.repository}:{class_record.commit_hash}'
        item_list = class_records_mapping.get(int_dict_key, list())
        class_records_mapping[int_dict_key] = [*item_list, class_record]
    print(sum([len(i) for i in class_records_mapping.values()]))

    method_records_mapping = dict()
    print(len(method_records))
    for method_record in method_records:
        int_dict_key = f'{method_record.repository}:{method_record.commit_hash}'
        item_list = method_records_mapping.get(int_dict_key, list())
        method_records_mapping[int_dict_key] = [*item_list, method_record]
    print(sum([len(i) for i in method_records_mapping.values()]))

    for i, repo_dict in enumerate(sub_repo_sorted_list):
        if repo_dict['repository'] in fukced_up_repos:
            continue
        try:
            logging.debug(f"Started calculating {repo_dict['repository']}")

            repo_name = get_repo_name(
                repo_dict['repository'], repo_dict['commit_hash'])
            repo_dir = repo_name[repo_name.index(
                "_") + 1:] + "-" + repo_dict['commit_hash']

            # download_form_gh(
            #     repo_dict['repository'], repo_dict['commit_hash'], DOWNLOAD_PATH)
            # with zipfile.ZipFile(path.join(DOWNLOAD_PATH, f'{repo_name}.zip'), "r") as zip_ref:
            #     zip_ref.extractall(DOWNLOAD_PATH)
            # result = subprocess.check_output(
            #     f'java -jar ck-master\\target\\ck-0.6.3-SNAPSHOT-jar-with-dependencies.jar {path.join(DOWNLOAD_PATH, repo_dir)} false 50 False', stderr=subprocess.STDOUT)
            # logging.debug(result)

            # if path.exists(path.join(DOWNLOAD_PATH, repo_dir)):
            #     logging.info(f"Removing {path.join(DOWNLOAD_PATH, repo_dir)}")
            #     rmtree(path.join(DOWNLOAD_PATH, repo_dir))
            # logging.debug("Cleared repo_dir")

            # copy("class.csv", path.join(RESULTS_PATH, f'class-{repo_dir}.csv'))
            # copy("method.csv", path.join(
            #     RESULTS_PATH, f'method-{repo_dir}.csv'))
            # logging.debug("Copied files")

            # os.remove("class.csv")
            # os.remove("method.csv")
            # logging.info(f"Clearing classes and methods")

            dict_key = f'{repo_dict["repository"]}:{repo_dict["commit_hash"]}'
            print(dict_key)
            class_metrics = generate_class_metric(
                path.join(RESULTS_PATH, f'class-{repo_dir}.csv'))
            method_metrics = generate_method_metric(
                path.join(RESULTS_PATH, f'method-{repo_dir}.csv'))

            if repo_dict["repository"] == "git@github.com:IBM/og.git":
                xd = {k: v for k, v in method_metrics.items()
                      if "com.ibm.og.guice.OGModule#provideRead" in k}
                print("xD , potrzebuje breakpoint")

            for class_record in class_records_mapping.get(dict_key, []):
                code_fragment_metrics = class_metrics[class_record.code_name]
                result_class_data = {
                    **{f'record_{key}': value for key, value in vars(class_record).items()},
                    **{f'metric_{key}': value for key, value in vars(code_fragment_metrics).items()}
                }
                class_results.append(result_class_data)

            for method_record in method_records_mapping.get(dict_key, []):
                code_fragment_metrics = method_metrics[method_record.code_name]
                result_method_data = {
                    **{f'record_{key}': value for key, value in vars(method_record).items()},
                    **{f'metric_{key}': value for key, value in vars(code_fragment_metrics).items()}
                }
                method_results.append(result_method_data)

        except Exception as e:
            raise e
            logging.error(
                f"Fukced up on {repo_dict['repository']} because {e}")

    logging.info("DONE DOWNLOADING AND PROCESSING REPOS")

    # logging.info(class_results, method_results)

    save_to_csv(class_results, "class_results.csv")
    save_to_csv(method_results, "method_results.csv")
    logging.info("DONE DONE")

    # logging.info(class_records)
    # logging.info(method_records)


if __name__ == "__main__":
    main()
