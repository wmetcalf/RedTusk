# AppArmor Profiles

## redtusk-worker

Confines the RedTusk worker container: allows the JVM, the fat JAR,
the AppCDS archive, the KSM native library, the scratch dir, and
the tesseract/zbarimg scanner binaries. Denies everything else.

### Load (once per host)

```bash
sudo apparmor_parser -r deploy/apparmor/redtusk-worker
```

Verify:
```bash
sudo apparmor_status | grep redtusk
```

### Apply to a container

```bash
docker run --security-opt apparmor=redtusk-worker ...
```
