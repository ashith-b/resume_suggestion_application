import numpy as np
import pandas as pd
import re
from sklearn.metrics.pairwise import cosine_similarity
from constants import RESUME_PATH, JD_PATH, JD_EMBEDDINGS_FILENAME, RESUME_EMBEDDINGS_FILENAME, \
    IS_EMBEDDINGS_CREATED
from directory_reader import DirectoryReader
from embedding_model import EmbeddingModel


def create_embeddings():
    """
    Reads job descriptions (JDs) and resumes, generates embeddings for each, and saves the embeddings to disk.
    """
    dir_reader = DirectoryReader(JD_PATH, RESUME_PATH)
    print("Reading JDs........")
    jd_data = dir_reader.read_jd_files()
    print("Reading Resumes........")
    resume_data = dir_reader.read_resume_files()
    print("Number of JDs -> ", len(jd_data))
    print("Number of Resumes -> ", len(resume_data))

    # Generate and Save JD Embeddings
    print("Generating embeddings for JDs........")
    embedding_model = EmbeddingModel()
    jd_embeddings = embedding_model.get_embeddings(jd_data)
    embedding_model.save_embeddings(jd_embeddings, JD_EMBEDDINGS_FILENAME)
    print("Embeddings generated from JDs")

    # Generate and Save Resume Embeddings
    print("Generating embeddings for Resumes........")
    resume_embeddings = embedding_model.get_embeddings(resume_data)
    embedding_model.save_embeddings(resume_embeddings, RESUME_EMBEDDINGS_FILENAME)
    print("Embeddings generated for Resumes")


def read_embeddings():
    """
    Reads job description and resume embeddings from disk.

    Returns:
        tuple: A tuple containing dictionaries of job description embeddings and resume embeddings.
    """
    embedding_model = EmbeddingModel()
    jd_embeddings = embedding_model.read_embeddings(JD_EMBEDDINGS_FILENAME)
    resume_embeddings = embedding_model.read_embeddings(RESUME_EMBEDDINGS_FILENAME)
    return jd_embeddings, resume_embeddings


def get_similarity_dict(jd_embeddings, resume_embeddings):
    """
    Computes cosine similarity between job description embeddings and resume embeddings.

    Args:
        jd_embeddings (dict): A dictionary of job description embeddings.
        resume_embeddings (dict): A dictionary of resume embeddings.

    Returns:
        dict: A dictionary where keys are resume names and values are dictionaries with job description names and their similarity scores.
    """
    resume_jd_combi_to_match = {"data_engineer": "de", "data_analyst": "dataanalyst",
                                "big_data_analyst": "bigdataanalyst",
                                "mlops_engineer": "mlops", "data_scientist": "ds", "data_architect": "da",
                                "machine_learning_engineer": "mle", "business_intelligence_analyst": "bianalyst"}

    jd_pattern = re.compile(r'\d+_[a-z]+$')
    resume_pattern = re.compile(r'_resume_\d+$')
    similarity_dict = {}
    for key1 in jd_embeddings.keys():
        for key2 in resume_embeddings.keys():
            cleaned_jd_category = jd_pattern.sub('', key1).replace('jd_data\\', '').replace('jd_data/', '')
            cleaned_resume_category = resume_pattern.sub('', key2)
            if resume_jd_combi_to_match[cleaned_resume_category] == cleaned_jd_category:
                sim_score = cosine_similarity(np.array(jd_embeddings[key1]).reshape(1, -1),
                                              np.array(resume_embeddings[key2]).reshape(1, -1))[0][0]
                if key2 not in similarity_dict.keys():
                    similarity_dict[key2] = {}
                similarity_dict[key2][key1] = {"score": sim_score}
            else:
                continue
    return similarity_dict


def get_top_matching_job(resume_name):
    """
    Finds the top matching job description for a given resume based on similarity scores.

    Args:
        resume_name (str): The name of the resume.

    Returns:
        list: A list containing the job description name and the matching score.
    """
    score_list = [[key, SIMILARITY_DICT[resume_name][key]['score']]
                  for key in SIMILARITY_DICT[resume_name].keys()]
    score_list = sorted(score_list, key=lambda x: x[1], reverse=True)
    return score_list[0]


if not IS_EMBEDDINGS_CREATED:
    create_embeddings()

jd_embeddings, resume_embeddings = read_embeddings()
SIMILARITY_DICT = get_similarity_dict(jd_embeddings, resume_embeddings)
output = []
for key in SIMILARITY_DICT.keys():
    top_matching_job = get_top_matching_job(key)
    output.append([key, top_matching_job[0], int(round(top_matching_job[1] * 100.0))])
    print("Resume Name: ", key, "\nJD Name: ", top_matching_job[0],
          "\nMatching Score: ", int(round(top_matching_job[1] * 100.0)))
    print("----------")

match_df = pd.DataFrame(output, columns=["resume_name", "jd_name", "matching_score"])
match_df.head(100)


get_top_matching_job("big_data_analyst_resume_1")