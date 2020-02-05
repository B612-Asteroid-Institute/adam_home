import sys
import adam
import urllib
import yaml

DEFAULT_PROD_URL = 'https://pro-equinox-162418.appspot.com/_ah/api/adam/v1'


def config(args):
    cm = adam.ConfigManager()

    # list config
    if args.list:
        print(cm)
        return

    # delete a key
    if args.delete:
        del cm[args.key]
        cm.to_file()
        return

    # set a key
    if args.value is not None:
        cm[args.key] = yaml.safe_load(args.value)
        cm.to_file()
        return

    # print a key
    if args.key is not None:
        *parents, key = args.key.split('.')
        res = {key: cm[args.key]}

        # build a tree (backwards)
        for k in reversed(parents):
            res = {k: res}

        # dump as yaml
        print(yaml.dump(res))
        return

    # print entire config (default action)
    print(cm)


def login(args):
    cm = adam.ConfigManager()

    def _do_login(name, url, no_browser):
        rest = adam.RestRequests(url)
        auth = adam.Auth(rest)

        # OAuth web flow page
        o = urllib.parse.urlparse(url)
        token_url = "%s://%s/%s" % (o.scheme, o.netloc, 'token.html')

        print("Setting up a service named '{}' with an endpoint at '{}'.".format(name, url))
        print("Please go to {} in your web browser, log in using a GMail or GSuite account, "
              "and paste below the token which will be shown to you at the end.".format(token_url)
              )
        if not no_browser:
            print("We'll try to automatically open a web browser for you (press ENTER to continue)")
            sys.stdin.readline()

            import webbrowser
            webbrowser.open(token_url)

        # user's token
        from getpass import getpass
        token = getpass("Token: ")

        if token and auth.authenticate(token):
            cm.set_config(name, dict(url=url, token=token))
            cm.to_file()
            print('Welcome, ' + auth.get_user())
        else:
            print('Could not authenticate user.')

    if args.name is not None:
        # log into a user-specified service
        _do_login(args.name, args.url, args.no_browser)
    else:
        # log into the defaut 'prod' environment
        _do_login('prod', DEFAULT_PROD_URL, args.no_browser)


def main(args=None):
    import argparse

    # adamctl
    parser = argparse.ArgumentParser(description='ADAM client command line utility')
    cmds = parser.add_subparsers(title='subcommands', dest='cmd')
    cmds.required = True

    # adamctl config
    config_cmd = cmds.add_parser('config', help='Manage configuration')
    config_cmd.add_argument('-l', '--list', action='store_true', help="show the full configuration")
    config_cmd.add_argument('--delete', action='store_true', help="delete the key")
    config_cmd.add_argument('key', type=str, help="config key to display or set", nargs='?')
    config_cmd.add_argument('value', type=str, help="value to be set, if given", nargs='?')
    config_cmd.set_defaults(func=config)

    # adamctl login
    login_cmd = cmds.add_parser('login', help='Log into an ADAM server')
    login_cmd.add_argument('name', help="name of the upstream ADAM server", nargs='?')
    login_cmd.add_argument('url', help="ADAM server URL", nargs='?')
    login_cmd.add_argument('--no-browser', action='store_true',
                           help="don't try to open a browser, just print the login page URL. "
                                "Useful when logging in on remote machines (e.g., via ssh)"
                           )
    login_cmd.set_defaults(func=login)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
