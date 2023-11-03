import pandas as pd
import openai
import json
import os
import streamlit as st
from cluster_skills import cluster_skills

from dotenv import load_dotenv
load_dotenv()

# Read the API key from an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def skills_to_json_list(*skills):
    """
    Convert skills into a JSON-encoded list.

    Args:
        *skills: Variable arguments of skill strings.

    Returns:
        str: A JSON-encoded string representing the list of skills.
    """
    return json.dumps(list(skills))


def call_openai_api(skills_text):
    """
    Make an API call to OpenAI to process the skills text.

    Args:
        skills_text (str): Text containing skills.

    Returns:
        list: Extracted skills from the text.
    """
    functions = [
        {
            "name": "skills_to_json_list",
            "description": "Convert a variable number of skills into a JSON-encoded list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skills": {
                        "type": "array",
                        "description": "A variable number of skill strings.",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["skills"]
            }
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': skills_text}],
            functions=functions,
            function_call={"name": "skills_to_json_list"}
        )
        arguments = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
        return arguments["skills"]
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return []


def extract_skills_from_csv(csv_path):
    """
    Extract skills from a CSV file using OpenAI API.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        set: Skills taxonomy.
        dict: Individual skills.
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"File not found: {csv_path}")
        return set(), {}

    df = df.head(2)
    skills_taxonomy = set()
    individual_skills = {}

    for _, row in df.iterrows():
        skills = call_openai_api(row['Skill Sets'])
        skills_taxonomy.update(skills)
        individual_skills[row['Name']] = skills

    return skills_taxonomy, individual_skills


def extract_skills_from_csv_in_realtime(uploaded_file):
    # Read the entire CSV
    df = pd.read_csv(uploaded_file)

    skills_taxonomy = set()
    individual_skills = {}
    table_placeholder = st.empty()  # Create a placeholder for the table

    # df = df.head(5)  # For demonstration, take only the first 5 rows

    # Process row-by-row
    for index, row in df.iterrows():
        skills = call_openai_api(row['Skill Sets'])
        skills_taxonomy.update(skills)
        individual_skills[row['Name']] = skills  # Store raw skills temporarily

    # Cluster skills
    skills_taxonomy_list = list(skills_taxonomy)
    clusters = cluster_skills(skills_taxonomy_list)
    
    # Create a mapping from the original skills to the cluster labels
    skill_to_cluster_label = {skill: cluster_name for cluster_name, skills in clusters for skill in skills}

    # Update skills_taxonomy to only include unique cluster labels
    skills_taxonomy = set(skill_to_cluster_label.values())

    # Update individual_skills with the clustered skills names
    for name, skills in individual_skills.items():
        clustered_skills = [skill_to_cluster_label.get(skill, skill) for skill in skills]
        individual_skills[name] = ', '.join(set(clustered_skills))  # Remove duplicates and convert to string

    # Update the table in the placeholder
    current_df = pd.DataFrame(list(individual_skills.items()), columns=['Name', 'Skills'])
    table_placeholder.table(current_df)

    return skills_taxonomy, individual_skills

"""
def extract_skills_from_csv_in_realtime(uploaded_file):
    # Read the entire CSV
    df = pd.read_csv(uploaded_file)

    skills_taxonomy = set()
    individual_skills = {}
    table_placeholder = st.empty()  # Create a placeholder for the table

    df = df.head(5)

    # Process row-by-row
    for index, row in df.iterrows():
        skills = call_openai_api(row['Skill Sets'])
        skills_taxonomy.update(skills)
        individual_skills[row['Name']] = ', '.join(skills)

        # Update the table in the placeholder
        current_df = pd.DataFrame(list(individual_skills.items()), columns=['Name', 'Skills'])
        table_placeholder.table(current_df)

    return skills_taxonomy, individual_skills
"""

def main():
    csv_path = "skills.csv"  # Replace with the path to your CSV

    skills_taxonomy, individual_skills = extract_skills_from_csv(csv_path)

    print("Skills Taxonomy:")
    for skill in skills_taxonomy:
        print(skill)

    print("\nIndividual Skills:")
    for name, skills in individual_skills.items():
        print(f"{name}: {', '.join(skills)}")


if __name__ == "__main__":
    main()
