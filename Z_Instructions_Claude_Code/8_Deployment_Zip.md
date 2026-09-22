I need to create a deployment zip of the backend/ folder for manual upload to AWS Elastic Beanstalk (since I don't have EB CLI permissions right now, using Console's "Upload and Deploy" instead).

Please:

Check backend/.gitignore (and the root .gitignore if it also applies to backend paths) to see what's excluded from version control.
Create a zip file at WeCare3.0/wecare-backend-deploy.zip containing everything inside backend/ EXCEPT anything matching the gitignore patterns (e.g., __pycache__, .env, media/, staticfiles/, *.pyc, local SQLite files if any, etc. — whatever's actually listed).
The zip's contents should be at the root level of the zip (i.e., manage.py, Dockerfile, requirements.txt, participants/, content/, journal/, wecare/, entrypoint.sh etc. should all be directly inside the zip, NOT nested inside a backend/ folder within the zip).
Confirm the final zip size and list its top-level contents so I can sanity-check before uploading to AWS.

Don't include .env — production environment variables are managed separately in the EB console, not deployed via this file.