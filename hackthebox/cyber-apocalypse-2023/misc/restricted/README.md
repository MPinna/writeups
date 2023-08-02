# Restricted

*You 're still trying to collect information for your research on the alien relic. Scientists contained the memories of ancient egyptian mummies into small chips, where they could store and replay them at will. Many of these mummies were part of the battle against the aliens and you suspect their memories may reveal hints to the location of the relic and the underground vessels. You managed to get your hands on one of these chips but after you connected to it, any attempt to access its internal data proved futile. The software containing all these memories seems to be running on a restricted environment which limits your access. Can you find a way to escape the restricted environment ?*
___

We have bash jail to which we can connect via ssh.

The source code and the Dockerfile are also available and in the Docker file we can see the following lines:

```docker
RUN ln -s /usr/bin/top /home/restricted/.bin
RUN ln -s /usr/bin/uptime /home/restricted/.bin
RUN ln -s /usr/bin/ssh /home/restricted/.bin
```

We can only run `top`, `uptime` and `run`.

We have to find a way to escape the jail.

We can't really use what https://gtfobins.github.io/gtfobins/top/ suggests since it requires to overwrite the `~/.config/procps/toprc` file but we can't do that since we have no permission to run `echo`.

The solution is actually quite simple: we can just try to run the `ssh` command passing it the flag as configuration file:

```
restricted@ng-restricted-avlkb-65bccf6cbb-2t4p7:~$ ssh -F ../../flag_8dpsy localhost
../../flag_8dpsy: line 1: Bad configuration option: htb{r35tr1ct10n5_4r3_p0w3r1355}
../../flag_8dpsy: terminating, 1 bad configuration options
```
