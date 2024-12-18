import json

import boto3

s3_client = boto3.client('s3')
# Assuming Bedrock client is available
bedrock_client = boto3.client('bedrock-runtime', region_name='us-west-2')
model_id = "us.amazon.nova-lite-v1:0"

prompt_template = """
Given the following transcript of a conversation, please analyze it and provide a concise summary, one-word sentiment, and a list of topics.

<transcription>
{transcript_text}
</transcription>

Format the output in JSON format and provide only the JSON output, nothing else.
<json_example>
{{
    "sentiment": "<sentiment>",
    "summary": "<concise_summary>",
    "topics": [
        {{
            "topic": "<short_topic>",
            "summary": "<brief_summary_of_topic>",
            "sentiment": "<sentiment_of_topic>"
        }}
    ]
}}
</json_example>
"""


def lambda_handler(event, context):
    try:
        # Get the bucket and object key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        # Check if the file is a '-transcript.json'
        if not key.endswith('-transcript.json'):
            print("Not a transcript JSON file. Exiting.")
            return

        # Get the transcription JSON file
        response = s3_client.get_object(Bucket=bucket, Key=key)
        transcription_data = json.loads(
            response['Body'].read().decode('utf-8'))

        # Parse the transcription into a simpler text format
        transcript_text = ""
        for item in transcription_data['results']['audio_segments']:
            speaker = item['speaker_label']
            transcript_text += f"{speaker}: {item['transcript']}\n"

        # Create a prompt template for the Bedrock LLM model
        prompt = prompt_template.format(transcript_text=transcript_text)
        messages = [{'role': 'user', 'content': [{'text': prompt}]}]
        inference_params = {"maxTokens": 400, "temperature": 0.1}

        # Call Bedrock Nova model to summarize the transcription
        response = bedrock_client.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig=inference_params,
        )
        summary = response['output']['message']['content'][0]['text']

        # Save the transcript summary to S3 with 'result.txt' in the filename
        summary_key = key.replace('-transcript.json', '-result.txt')
        s3_client.put_object(Bucket=bucket, Key=summary_key, Body=summary)
        print(f"Summary saved to {summary_key}")

    except Exception as e:
        print(f"Error processing file {key}: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('Summary job completed.')
    }
