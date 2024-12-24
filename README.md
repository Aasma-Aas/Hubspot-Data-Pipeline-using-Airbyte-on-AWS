<h1 align="center" style="color: #073763; text-align: center;">HubSpot Data Pipeline using Airbyte</h1>
<br></br>

## <span style="color: #073763;">Introduction</span>

This project sets up a data pipeline for a HubSpot app, installed by multiple users, to extract and process targeted user data. The pipeline utilizes Airbyte connectors, AWS Glue for transformation, and AWS services for storage and reporting. The whole process consists of the following steps:

1. Store user accounts data in DB
2. Configure Airbyte for Data Extraction
3. Data transformation with AWS Glue
4. Store the data in S3

## <span style="color: #073763;">Architecture</span>

<p align="center">
    <img src="https://github.com/user-attachments/assets/9bbe137b-6dd2-451d-ab04-f31670450e7e" alt="Architecture Diagram" width="500" style="display: flex;">
</p>

### <span style="color: #073763;">1. HubSpot</span>
The application is built using the Flask framework in Python, which uses credentials from a HubSpot public developer account. The app supports OAuth 2.0 configuration, allowing multiple scopes to be defined for retrieving data from various categories (such as companies, deals, campaigns, etc.).

Users will access the application and authenticate using their HubSpot standard account. Upon authentication (or app installation), a refresh token will be generated for the user. This refresh token will then be used by the Airbyte console to create the connector and synchronize the data.

In our application, we will be storing three types of data:

- **Username**: To seek the name of the account holder
- **Hub_id**: A unique ID allocated with each standard account, allowing identification of multiple accounts under the same username
- **Refresh Token**: This will be used in Airbyte to create the source connector and synchronize the data

### <span style="color: #073763;">2. Airbyte</span>
Airbyte will be configured to extract data from HubSpot and store it in Amazon S3. The setup involves creating connectors for each user, defining generic data streams, and specifying the schema for each stream. For example, a stream like "Contacts" may include fields such as ID, name, and email.

To create a connector, both a source and a destination are required:

- **Source**: HubSpot – where the data will be extracted from
  - **Client_id**: HubSpot developer account client ID
  - **Client_secret**: HubSpot developer account client secret
  - **Refresh_token**: A unique refresh token for each user

- **Destination**: Amazon S3 Bucket – where the extracted data will be stored

Each user will have a unique connector, configured with a distinct refresh token. This allows Airbyte to extract data specific to that user's HubSpot account. For example, if there are 150 users, Airbyte will create 150 separate connectors, each customized to the individual user's credentials and data. This ensures that data extraction is accurate and specific to each account, preventing overlap or data confusion, while maintaining a seamless flow of data from HubSpot to Amazon S3.

### <span style="color: #073763;">3. AWS</span>
In the S3 bucket, the extracted data will be stored as Parquet files. The data will be partitioned by user, with each user having a dedicated folder. Each folder will further be subdivided into stream categories such as companies, deals, campaigns, etc.

For data cleaning and transformation, an AWS Glue job will be scheduled to process and clean the data as the files become available. The job will ensure the data is properly cleaned and transformed before further analysis or storage.

## <span style="color: #073763;">Steps to Setup the Pipeline</span>

1. **Set up HubSpot OAuth Application**:
   - Create a HubSpot OAuth application and get your `client_id`, `client_secret`, and set up OAuth 2.0 scopes for required permissions.
   
2. **Configure Airbyte**:
   - Set up an Airbyte instance.
   - Create a connector for each user by providing the required `client_id`, `client_secret`, and the unique `refresh_token` for each user.
   - Set up the destination to an Amazon S3 bucket.

3. **Configure AWS Glue**:
   - Set up an AWS Glue job to process and clean the data stored in Amazon S3.
   - Ensure the Glue job is scheduled to run periodically or trigger based on new data arrival.

4. **Test and Monitor the Pipeline**:
   - Ensure that data is being correctly extracted, stored, and cleaned.
   - Monitor the Airbyte connectors for any issues and ensure the data in the S3 bucket is up to date and properly cleaned.

## <span style="color: #073763;">Conclusion</span>

This data pipeline ensures that user data from HubSpot is extracted, transformed, and stored in a structured format in Amazon S3. The use of Airbyte connectors, AWS Glue, and S3 enables scalable and efficient data processing, which can later be used for reporting and analysis.
