## Week 4 Azure Data Factory Assignment
# Objective
Build an end-to-end data pipeline using Azure Blob Storage and Azure Data Factory.

## Services Used
- Azure Resource Group
- Azure Storage Account
- Azure Blob Storage
- Azure Data Factory
- IAM Roles

## Dataset
Superstore Dataset (CSV)

## Pipeline Flow

Source CSV (Blob Storage)
        ↓
Get Metadata
        ↓
Copy Data
        ↓
Destination Blob Storage

## Activities Performed

1. Created Resource Group
2. Created Storage Account
3. Created Blob Containers
4. Uploaded CSV File
5. Created Azure Data Factory
6. Configured Linked Service
7. Created Source and Destination Datasets
8. Implemented Get Metadata Activity
9. Implemented Copy Data Activity
10. Executed Pipeline Successfully
11. Configured IAM Roles

##Mini Project Summary

An end-to-end data pipeline was built using Azure Blob Storage and Azure Data Factory. The source CSV file (Superstore dataset) was uploaded to Azure Blob Storage. A Linked Service and datasets were created to establish connectivity between Azure Data Factory and Blob Storage.
A Get Metadata activity was used to validate the source file and retrieve file information such as existence, size, and last modified date. A Copy Data activity was then configured to copy the source file from the source container to a destination container.
The pipeline was executed successfully, and the output file was generated in the destination location. This project demonstrated Azure cloud fundamentals, storage management, metadata validation, data movement, and pipeline orchestration using Azure Data Factory.    

## Result

- Metadata validated successfully
- Data copied successfully
- Pipeline executed successfully
