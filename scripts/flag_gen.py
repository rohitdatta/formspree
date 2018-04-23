import glob, os
os.chdir("../formspree/static/img/flags/16")
for file in sorted(glob.glob("*.png")):
    if len(file) != 6:
        continue
    print "#country.%s::before {\n  background: url('/static/img/flags/16/%s');\nbackground-repeat:no-repeat;\n}\n" % (file[:2], file)