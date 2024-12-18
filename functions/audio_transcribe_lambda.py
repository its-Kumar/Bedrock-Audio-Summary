import json
import time

import boto3

s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')


def lambda_handler(event, context):
    # Get the bucket and object key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Check if the file is an .mp3
    if not key.endswith('.mp3'):
        print("Not an mp3 file. Exiting.")
        return

    # Start transcription job
    job_name = key.split('/')[-1].split('.')[0] + '_transcription'
    job_uri = f's3://{bucket}/{key}'

    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat='mp3',
        LanguageCode='en-US',
        Settings={
            'ShowSpeakerLabels': True,
            'MaxSpeakerLabels': 2
        }
    )

    # Wait for the transcription job to complete
    while True:
        status = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in [
                'COMPLETED', 'FAILED']:
            break
        print("Waiting for transcription to complete...")
        time.sleep(5)

    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        # Get the transcription result
        transcription_url = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        transcription_response = s3_client.get_object(
            Bucket=bucket, Key=transcription_url.split('/')[-1])
        transcription_data = json.loads(
            transcription_response['Body'].read().decode('utf-8'))

        # Save the transcription to S3 with '-transcript.json' suffix
        transcription_key = key.replace('.mp3', '-transcript.json')
        s3_client.put_object(
            Bucket=bucket,
            Key=transcription_key,
            Body=json.dumps(transcription_data))
        print(f"Transcription saved to {transcription_key}")
    else:
        print("Transcription job failed.")

    return {
        'statusCode': 200,
        'body': json.dumps('Transcription job completed.')
    }
  
