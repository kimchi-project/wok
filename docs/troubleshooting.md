## Troubleshooting

* [Firewall](#firewall)
* [SELinux](#selinux)

### Firewall
Wok uses by default the ports 8000 and 8001. To allow incoming connections:

    For system using firewalld, do:

        $ sudo firewall-cmd --add-port=8000/tcp --permanent
        $ sudo firewall-cmd --add-port=8001/tcp --permanent
        $ sudo firewall-cmd --reload

    For openSUSE systems, do:

        $ sudo /sbin/SuSEfirewall2 open EXT TCP 8000
        $ sudo /sbin/SuSEfirewall2 open EXT TCP 8001

    For system using iptables, do:

        $ sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
        $ sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT

    Don't forget to correctly save the rules.

### SELinux
Allow httpd_t context for Wok web server:

    $ sudo semanage permissive -a httpd_t
