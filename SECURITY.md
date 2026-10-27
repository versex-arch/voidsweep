# Security policy

Voidsweep deletes files, so bugs that make it offer or remove something it should not are treated as security issues — even if no attacker is involved.

Please report them privately through **GitHub → Security → Report a vulnerability** on this repository rather than in a public issue. Include the OS, the path involved and the marker code shown.

In scope:
- an item outside the documented locations being offered or removed;
- a protected path (home, user folders, system folders, keychains, backups…) passing the guard;
- the local API being reachable without the per-launch token, or from another origin.
