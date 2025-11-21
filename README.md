# serverless-image-processing-pipeline-alison-soares

This project implements a serverless image processing pipeline using AWS services.

## Short-Diagram


+-------------+      +-------------------------+      +--------------------+      +------------------------------+
|  Client     | ---> | API Gateway (REST API) | ---> | Step Functions      | ---> | Lambda: resize-image-function|
+-------------+      +-------------------------+      +--------------------+      +------------------------------+
                                                                                           |
                                                                                           v
                                                                               +------------------------+
                                                                               | S3 (resized-images)    |
                                                                               +------------------------+

S3 (original-images) stores the original uploads used as input.

# Detailed flow diagram (with optional mermaid code diagram saved in docs)

Serverless application that resizes images uploaded to Amazon S3 using AWS Lambda, Step Functions, and API Gateway.  
Original images are stored in one bucket and resized thumbnails are written to a second bucket, all orchestrated through a state machine and exposed by an HTTP endpoint.


High-level flow:

1. Client sends an HTTP `POST` request to the API Gateway endpoint `/prod/resize` with JSON describing the source and destination S3 buckets, object key, and target size.
2. API Gateway calls Step Functions `StartExecution`, passing the JSON body as the `input`.
3. The `ImageResizeStateMachine` runs:
   - Task state invokes the Lambda function `alison-image-resizer`.
   - Choice state checks the Lambda response to decide between Success or Fail.
4. The Lambda function:
   - Downloads the original image from `alison-image-originals-01`.
   - Uses Pillow to create a thumbnail.
   - Uploads the thumbnail to `alison-image-thumbnails-01` under `thumbnails/<width>x<height>_<filename>`.
5. Step Functions returns the execution result to API Gateway, which returns an HTTP 200 response with the `executionArn` to the client.

### Mermaid diagram

```mermaid
flowchart LR

    subgraph Client["Client"]
        C1["PowerShell / curl / Postman"]
    end

    subgraph APIGW["API Gateway\nalison-image-resize-api"]
        A1["POST /prod/resize"]
    end

    subgraph SFN["AWS Step Functions\nImageResizeStateMachine"]
        S1["ResizeImage (Task)\n→ Lambda"]
        S2["CheckStatus (Choice)\nSUCCESS / FAIL"]
    end

    subgraph LAMBDA["AWS Lambda"]
        L1["alison-image-resizer\n(Python 3.9 + Pillow layer)"]
    end

    subgraph S3["Amazon S3"]
        O["alison-image-originals-01\n(original images)"]
        T["alison-image-thumbnails-01\n(thumbnails/128x128_*.jpg)"]
    end

    C1 -->|"JSON request\n{ source_bucket, destination_bucket,\n  object_key, width, height }"| A1
    A1 -->|"StartExecution\n(stateMachineArn, input, name)"| SFN
    SFN -->|"Task: Invoke\nalison-image-resizer"| L1

    L1 -->|"GET object\nexample.jpg"| O
    L1 -->|"PUT object\nthumbnails/128x128_example.jpg"| T

    L1 -->|"status: SUCCESS / FAILED"| SFN
    SFN -->|"Execution result\n(200 + executionArn)"| A1
    A1 -->|"HTTP 200\nexecutionArn, startDate"| C1
