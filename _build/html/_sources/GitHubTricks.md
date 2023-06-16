- [Quick push of new additions/changes from a local repo into github](#quick-push-of-new-additionschanges-from-a-local-repo-into-github)
- [How to Update a Local Fork at the Terminal/Command Line Interface(CLI)](#how-to-update-a-local-fork-at-the-terminalcommand-line-interfacecli)

## Quick push of new additions/changes from a local repo into github

```
git add . #be sure to be in the folder containing the modifications
git commit -m "some message"
git push
```

## How to Update a Local Fork at the Terminal/Command Line Interface(CLI)

Useful when having forked a repo and wishing to keep pace from the CLI: 

(credits: [Sunil Kumar Sahoo](https://medium.com/@sahoosunilkumar/how-to-update-a-fork-in-git-95a7daadc14e))
![GitHub fork's management](figures/githubfork.png)

```
# Verify the remote branch attached for fetch and push operation using following command 
git remote -v
# Specify a remote upstream repo to sync with your fork
git remote add upstream https://github.com/OriginalRepo/OriginalProject.git
# Verify again using 
git remote -v
# Fetch branches and commits from the upstream repo. You’ll be storing the commits to master in a local branch upstream/master using following command: 
git fetch upstream
# Checkout your fork’s local master 
git checkout master
# Merge changes from upstream/master into it 
git merge upstream/master
# Push changes to update your fork master on Github
git push origin master
```