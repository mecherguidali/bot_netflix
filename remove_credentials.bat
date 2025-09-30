@echo off
echo This script will help remove the credentials file from Git history

echo Step 1: Create a backup of your repository
mkdir ..\bot_netflix_backup
xcopy /E /I /H /Y . ..\bot_netflix_backup

echo Step 2: Remove the credentials file from Git tracking
git rm --cached bot-netflix-473417-473511-10bd9ccf6f87.json

echo Step 3: Create a new commit without the credentials file
git commit -m "Remove credentials file from tracking"

echo Step 4: Create a new branch without the credentials
git checkout --orphan temp_branch

echo Step 5: Add all files to the new branch
git add .

echo Step 6: Commit the changes
git commit -m "Initial commit without credentials"

echo Step 7: Delete the old main branch
git branch -D main

echo Step 8: Rename the current branch to main
git branch -m main

echo Step 9: Force push to GitHub
git push -f origin main

echo Done! The credentials file should now be completely removed from your Git history.
echo If you still have issues, please contact GitHub support.
