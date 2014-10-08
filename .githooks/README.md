## What Are Git Hooks?

> _For a general guide to git hooks, see [Pro Git](http://git-scm.com/book/en/Customizing-Git-Git-Hooks), by Scott Chacon._

This directory contains git hooks for post-merge and pre-commit. Once the hooks are put into place in your local git repo, they will automatically run. 

### Installing Git Hooks

To use these git hooks, soft link the `.githooks` directory into the appropriate location within your NuPIC repository. The following line shows how to link this directory into the git configuration in the right place.

    ln -s /path/to/nupic/.githooks /path/to/nupic/.git/hooks

> **NOTE**: _When installed, git may have pre-populated the `.git/hooks` directory with some sample scripts. You may need to `rm -rf .git/hooks` before the link command above will work.

### Pre-Commit

The pre-commit file is executed before each commit and the commit fails if it
returns a non-zero exit code.  This can be overridden by committing files as
follows:

    git commit --no-verify ...

### Post-Merge

After merging, you'll be notified if you need to rebuild.
