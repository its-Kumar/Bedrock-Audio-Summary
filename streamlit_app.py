import os
import time

import boto3
import streamlit as st

# AWS S3 configuration
s3_client = boto3.client('s3')
bucket_name = 'da-aws-iot-poc-15626'


def check_file_exists(bucket, key):
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except s3_client.exceptions.NoSuchKey:
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


st.set_page_config(page_title="Audio AI", page_icon="🔉", layout='wide')

# Streamlit application
st.title("Audio Summarization")
st.info("Analyze the conversation between the sales representative and the customer, summarize it, and identify any issues.")
st.write("Powered by AWS Serverless Event Driven Architecture and Amazon Bedrock’s Large Language Models (LLMs) for advanced natural language processing.")

# Upload MP3 file
uploaded_file = st.file_uploader("Upload an MP3 file", type=["mp3"])

if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    temp_file_path = os.path.join("temp", uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Show audio player
    st.audio(temp_file_path)

    # Upload the file to S3
    upload_key = "kumar/" + uploaded_file.name

    # Download another text file from S3
    uploaded_file_name = uploaded_file.name.split('.')[0]
    text_file_key = f'kumar/{uploaded_file_name}-result.txt'
    text_file_path = os.path.join("temp", f"{uploaded_file_name}-result.txt")

    print(text_file_key)
    if check_file_exists(bucket_name, text_file_key):
        time.sleep(3)
        s3_client.download_file(bucket_name, text_file_key, text_file_path)
    else:
        s3_client.upload_file(temp_file_path, bucket_name, upload_key)
        st.success(
            f"File {uploaded_file.name} uploaded.")
        time.sleep(50)
        s3_client.download_file(bucket_name, text_file_key, text_file_path)

    st.subheader("Results:")
    # Display the content of the text file
    with open(text_file_path, "r") as f:
        text_content = f.read()

    st.code(text_content, wrap_lines=True)

    # Clean up temporary files
    os.remove(temp_file_path)
    os.remove(text_file_path)
