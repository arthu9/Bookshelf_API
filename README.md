# BookShelf (REST-API Server) #

### Installation ###

Start with `https://github.com/arthu9/BookshelfV2-API.git`

### Development workflow ###

We are using the Git Flow
https://guides.github.com/introduction/flow/

The requested workflow would be:
When you start to work on a new card (assuming the previous one been finished and pushed):
```
git checkout master
git pull
git checkout -b <newbranchname>
```
'newbranchname' should be the Trello task name. For example:  git checkout -b task_feature
The recommendation is to do the git add and git commit -m "<what step has been done>" frequently.
If the task takes several days the recommended to do git push on every other day.
When the job declared on card is finished then do a git push
Then log in to github.com and request a merge from the branch.
