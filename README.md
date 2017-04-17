## f
A favorite folder facility

### Install
The `install.sh` script will create `~/.f` and link `f.py` to this directory, and wrap `f.py` in a function in `
.bashrc`.

``` bash
git clone git@github.com:pengmeng/f.git
cd f && sh install.sh
# init f
f --init
```

### Usage
For help:  

``` bash
f -h
usage: f.py [-h] [-f FAVORITE] [-l] [-d DELETE] [--init]    
                                                            
optional arguments:                                         
  -h, --help            show this help message and exit     
  -f FAVORITE, --favorite FAVORITE                          
                        add current dir to favorite with tag
  -l, --listall         list all memorized dirs             
  -d DELETE, --delete DELETE                                
                        delete a dir with full tag          
  --init                init f                              
```

To add current directory to favorite, simply type `f`.  

To add current directory to favorite with tag:  

```bash
f -f my_favorite_dir
```

To jump to a directory by tag or unique prefix of tag:  

```bash
f my_favorite_dir
# or
f my
```

If prefix is not unique, f will list all matched directories.  

To list all favorite and frequently use directories (from most frequent to least), and type tag to jump:  

```bash
f -l
1       /Users/pengmeng/work/cube/fanout
0       /Users/pengmeng/Desktop         
2       /Users/pengmeng/code            
Enter a tag to jump:                    
1                                       
```

To delete, only accept full tag when delete:  
```bash
f -d my_favorite_dir
```