# Handling secrets

We strongly recommend **not** putting any sensitive information such as passwords or private keys into your repository. This page describes the helpers available in BundleWrap to manage those secrets without checking them into version control.

<div class="alert alert-info">Most of the functions described here return lazy <a href="../api/#bundlewraputilsfault">Fault objects</a>.</div>

<br>

## .secrets.cfg

When you initially ran `bw repo create`, a file called `.secrets.cfg` was put into the root level of your repo. It's an INI-style file that by default contains two random keys BundleWrap uses to protect your secrets. One for randomly generated passwords, one for symmetric encryption.

<div class="alert alert-danger">You should never commit <code>.secrets.cfg</code>. Immediately add it to your <code>.gitignore</code> or equivalent.</div>

<br>

## Derived passwords

In some cases, you can control (i.e. manage with BundleWrap) both ends of the authentication process. A common example is a config file for a web application that holds credentials for a database also managed by BundleWrap. In this case, you don't really care what the password is, you just want it to be the same on both sides.

To accomplish that, just write this in your template (Mako syntax shown here):

<pre><code class="nohighlight">database_user = "foo"
database_password = "${repo.vault.password_for("my database")}"
</code></pre>

In your bundle, you can then configure your database user like this:

	postgres_roles = {
	    "foo": {
	        'password': repo.vault.password_for("my database"),
	    },
	}

It doesn't really matter what string you call `password_for()` with, it just has to be the same on both ends. BundleWrap will then use that string, combine it with the default key called `generate` in your `.secrets.cfg` and derive a random password from that.

This makes it easy to change all your passwords at once (e.g. when an employee leaves or when required for compliance reasons) by rotating keys.

<div class="alert alert-warning">However, it also means you have to guard your <code>.secrets.cfg</code> very closely. If it is compromised, so are <strong>all</strong> your passwords. Use your own judgement.</div>

### "Human" passwords

As an alternative to `password_for()`, which generates random strings, you can use `human_password_for()`.It generates strings like `Wiac-Kaobl-Teuh-Kumd-40`. They are easier to handle for human beings. You might want to use them if you have to type those passwords on a regular basis.

### Random bytes

`password_for()` and `human_password_for()` are meant for passwords. If you need plain random bytes, you can use `random_bytes_as_base64_for()`. As the name implies, it will return the data base64 encoded. Some examples:

<pre><code class="nohighlight">$ bw debug -c 'print(repo.vault.random_bytes_as_base64_for("foo"))'
qczM0GUKW7YlXEuW8HGPYkjCGaX4Vu9Fja5SIZWga7w=
$ bw debug -c 'print(repo.vault.random_bytes_as_base64_for("foo", length=1))'
qQ==
</code></pre>

<br>

## Static passwords

When you need to store a specific password, you can encrypt it symmetrically. The `bw pw` utility provides command line access to the functions attached to `repo.vault`, so we'll use it here to generate the encrypted string:

<pre><code class="nohighlight">$ bw pw --encrypt 'my password'
gAAAA[...]mrVMA==
</code></pre>

You can then use this encrypted password in a template like this:

<pre><code class="nohighlight">database_user = "foo"
database_password = "${repo.vault.decrypt("gAAAA[...]mrVMA==")}"
</code></pre>

<br>

## Files

You can also encrypt entire files:

<pre><code class="nohighlight">$ bw pw --encrypt --file encrypted.file /my/secret.file</code></pre>

<div class="alert alert-info">Encrypted files are always read and written relative to the <code>data/</code> subdirectory of your repo.</div>

If the source file was encoded using UTF-8, you can then simply pass the decrypted content into a file item:

	files = {
	    "/secret": {
	        'content': repo.vault.decrypt_file("encrypted.file"),
	    },
	}

If the source file is binary however (or any encoding other than UTF-8), you must use base64:

	files = {
	    "/secret": {
	        'content': repo.vault.decrypt_file_as_base64("encrypted.file"),
	        'content_type': 'base64',
	    },
	}

<br>

## External commands

To retrieve secrets using a local shell command, use `vault.cmd`:

<pre><code class="nohighlight">$ bw debug -c "print(repo.vault.cmd('uname'))"
Linux</code></pre>

By default, the stdout of the given command will be decoded to text using UTF-8 and have leading and trailing whitespace stripped. To prevent this, use the `as_text` and `strip` parameters:

<pre><code class="nohighlight">$ bw debug -c "print(repo.vault.cmd('uname', as_text=False, strip=False))"
b'Linux\n'</code></pre>

The point of using `repo.vault.cmd()` is that (like the other functions introduced on this page) it will return a lazy `Fault` object that will call the command only if and when the value is actually needed (e.g. when rendering a file template).

<br>

## Key management

### Multiple keys

You can always add more keys to your `.secrets.cfg`, but you should keep the defaults around. Adding more keys makes it possible to give different keys to different teams. **By default, BundleWrap will skip items it can't find the required keys for**.

When using `.password_for()`, `.encrypt()` etc., you can provide a `key` argument to select the key:

	repo.vault.password_for("some database", key="devops")

On the command line, `bw pw` also accepts `--key` for this purpose.

The encrypted data will be prefixed by `yourkeyname$...` to indicate that the key `yourkeyname` was used for encryption. Thus, during decryption, you can omit the `key=` parameter.

<br>

### Rotating keys

You can generate a new key by running `bw debug -c "print(repo.vault.random_key())"`. Place the result in your `.secrets.cfg`. Then you need to distribute the new key to your team and run `bw apply` for all your nodes.

<div class="alert alert-info">Note that `encrypt()` and `decrypt()` (plus their `file_` counterparts) use symmetric encryption and require manually updating the encrypted text after the key has changed.</div>
