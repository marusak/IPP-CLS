# !/usr/bin/python3
# coding=utf-8
"""xmarus06 STUFF."""
from __future__ import print_function
import sys
import re
from lxml.etree import Element, SubElement, tostring
from xml.dom import minidom

# TODO test kde --detail na nieco co neexistuje -- len hlavicka //FORUM
# TODO viackrat using na to iste z jednej/z dvoch tried?i, chyba base class, je private...

# ---------
# TODO 6(obcas ano, obcas nie - !!), 11 FORUM, 12 nepodporujem zatial
# TODO privatne sa dedia ale nevypisuju (kvoli konfliktom) !! test z fora k test03 !!
# TODO ak pri search neewxistuje, vypise sa len hlavicka//FORUM
# TODO viackrat using na to iste z jednej/z dvoch tried?


def error(message, error_code):
    """Print exit message to stderr and exit."""
    print(message, file=sys.stderr)
    sys.exit(error_code)


def help():
    """Print help and exit."""
    print("HELP")  # TODO more help
    exit(0)


def prettify(elem, n):
    """Return a pretty-printed XML string - from pymotw.com."""
    if (isinstance(elem, str)):
        return (" "*n+elem)
    rough_string = tostring(elem)
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent=" "*n)


def parseCommandLine(cmd_line):
    """Parse command line.

    cmd_line: list of arguments without script name
    return :
    """
    result = {}
    for arg in cmd_line:
        matches = re.search("^--((\w|-)*)(=([^\s]+))?$", arg)
        if (matches is None):
            error("Dude, thats not even argument", 1)
        if (matches.group(1) in result.keys()):
            error("Common, I already got it, no need to tell me twice", 1)
        if (matches.group(1) not in ("help", "input", "output", "pretty-xml",
           "details", "search", "conflicts")):
            error("Holy moly, what was that?!", 1)
        if ((matches.group(4) == "" or matches.group(4) is None) and
            matches.group(1) != "details" and matches.group(1) != "pretty-xml" and
           matches.group(1) != 'help'):
            error("I/O, details and search need som additional info", 1)
        if (matches.group(1) == 'help' and matches.group(4) != ""):
            error("Help does not take any arguments", 1)
        result[matches.group(1)] = matches.group(4)
    return result


def getToken(acc):
    """Return one token."""
    result = re.match("\s*(\w+|\{|\}|\(|\)|;|\=|,|:|\*|&|~)\s*([\s\S]*)", acc)
    if (result is None):
        error("Token nepozna typ "+acc+"\n", 69)
    if (result.group(1) == ":" and result.group(2)[0] == ":"):  # ::
        return ("::", result.group(2)[1:])
    else:
        return (result.group(1), result.group(2))


def getType(token, cls):
    """Return type of variable or function."""
    acc_type = ""
    while True:  # simulation do-while
        acc_type = acc_type + token + " "
        token, cls = getToken(cls)
        if (token not in
            ("void", "bool", "char", "int", "float", "double", "void",
             "wchar_t", "signed", "unsigned", "short", "long", "*", "&")):
            return (acc_type[:-1], token+" "+cls)


def getFArgs(cls):
    """Parse function arguements."""
    f_arg_types = ()
    f_arg_names = ()
    token = ""
    while (token != ")"):
        token, cls = getToken(cls)
        if (token == ")"):
            return (cls, f_arg_names, f_arg_types)
        arg, cls = getType(token, cls)  # type
        if (arg == "void"):
            name, cls = getToken(cls)  # )
            return (cls, f_arg_names, f_arg_types)
        name, cls = getToken(cls)  # name
        token, cls = getToken(cls)  # comma or )
        f_arg_types = f_arg_types + (arg,)
        f_arg_names = f_arg_names + (name,)
    return (cls, f_arg_names, f_arg_types)


def parseClasses(cls):
    """Berie cely vstup, rozprasuje ho na triedy a vlozi to do struktury.

    Returns list of classes, where each class consists from:
    key = name
    [0] = list of parents (ClassName, type)
    [1] = methods ((Name, arguments_types) return_type, argumenst_names defined/declared,
        virtual, pureVirtual, privacy, static, from)
    [2] = instances((Name), type, defined/declared, virtual, privacy,static,from)
    [3] = usings [1] methods (name, arguments_types) from, privacy, argumenst_names
                 [2] instances (name) from, privacy
    """
    classes = {}
    while (cls != ""):
        token, cls = getToken(cls)
        if (token != "class"):
            error("Musi byt class", 4)
        # name
        className, cls = getToken(cls)
        token, cls = getToken(cls)
        parents = {}
        methods = {}
        instances = {}
        usingM = {}
        usingI = {}
        while (token != "{" and token != ";"):
            token, cls = getToken(cls)  # comma, no control
            # read the inheritance
            if (token in ("private", "protected", "public")):
                papaName, cls = getToken(cls)
                if papaName not in classes.keys():
                    error("Neda sa dedit z triedy, ktora neexistuje", 4)
                if classes[papaName] == 'declared':
                    error("Neda sa dedit z triedy, ktora je len deklarovana", 4)
                if (papaName in parents.keys()):
                    error("Duplicate base class", 4)
                parents[papaName] = token
            else:
                if token not in classes.keys():
                    error("Neda sa dedit z triedy, ktora neexistuje", 4)
                if classes[token] == 'declared':
                    error("Neda sa dedit z triedy, ktora je len deklarovana", 4)
                parents[token] = "private"
            token, cls = getToken(cls)

        # declaration -> moze sposobit problemy len v takejto forme
        if (token == ";"):  # only class declaration
            if (className not in classes.keys()):
                classes[className] = "declared"
                continue
            else:
                continue

        # implicitly private
        privacy = "private"
        token, cls = getToken(cls)
        # till the end of actuall class
        # one loop = one method or instance or privacy modifier
        while (token != "}"):
            virtual = False
            static = False
            if (token == "virtual"):
                virtual = True
                token, cls = getToken(cls)
            if (token == "static"):
                static = True
                token, cls = getToken(cls)

            if (token in ("private", "protected", "public")):
                privacy = token
                token, cls = getToken(cls)  # :, no control
                token, cls = getToken(cls)
                continue
            if (token == "using"):
                fromName, cls = getToken(cls)
                token, cls = getToken(cls)  # ::
                whatName, cls = getToken(cls)
                token, cls = getToken(cls)  # ; or (
                if (token == ";"):
                    usingI[whatName] = (fromName, privacy)
                    token, cls = getToken(cls)
                    continue
                elif (token != "("):
                    error("Dont know type", 4)
                cls, f_arg_names, f_arg_types = getFArgs(cls)
                token, cls = getToken(cls)  # ;
                token, cls = getToken(cls)
                usingM[whatName, f_arg_types] = (fromName, privacy, f_arg_names)
                continue
            if (token == "~"):  # Destructor
                name, cls = getToken(cls)
                if (name != className):
                    error("Destructor but with wrong name", 4)
                name = "~"+name
                token, cls = getToken(cls)
                token, cls = getToken(cls)
                if (token != ")"):
                    error("Destructor does not have any arguments", 4)
                token, cls = getToken(cls)
                if (token == ";"):
                    if ((name, ()) in methods.keys()):
                        error("Overloading of destructor", 4)
                    methods[name, ()] = ["void", (), "declared", virtual,
                                         False, privacy, static, className]
                    token, cls = getToken(cls)
                    continue
                token, cls = getToken(cls)  # }
                if (token != "}"):
                    print (token)
                    print (cls)
                    error("What was that, destructor stuff", 4)
                token, cls = getToken(cls)
                if (token == ";"):
                    token, cls = getToken(cls)
                if ((name, ()) in methods.keys()):
                    error("Redefinicia destuktoru", 4)
                methods[name, ()] = ["void", (), "defined", virtual,
                                     False, privacy, static, className]
                continue
            if (token == className):  # Contructor
                name = token
                token, cls = getToken(cls)
                f_arg_types = ()
                f_arg_names = ()
                cls, f_arg_names, f_arg_types = getFArgs(cls)
                token, cls = getToken(cls)
                if (token == ";"):  # constructor declaration
                    if ((name, f_arg_types) in methods.keys()):
                        error("Overloading of constructor", 4)
                    methods[name, f_arg_types] = [name, f_arg_names,
                                                  "declared", virtual,
                                                  False, privacy, static,
                                                  className]
                    token, cls = getToken(cls)
                    continue
                token, cls = getToken(cls)  # {
                if (token != "}"):
                    error("What was that, constructor stuff", 4)
                token, cls = getToken(cls)
                if (token == ";"):
                    token, cls = getToken(cls)
                if ((name, f_arg_types) in methods.keys()):
                    error("Redefinicia constructoru", 4)
                methods[name, f_arg_types] = [name, f_arg_names, "defined",
                                              virtual, False, privacy,
                                              static, className]
                continue
            acc_type, cls = getType(token, cls)  # get type
            token, cls = getToken(cls)  # get name
            acc_name = token
            token, cls = getToken(cls)
            if (token == ";"):  # instance declaration
                if (acc_name in instances.keys()):
                    error("Overloading of instance", 4)
                instances[acc_name] = [acc_type, "declared", virtual,
                                       privacy, static, className]
                token, cls = getToken(cls)
                continue
            if (token == "="):  # instance definition
                while (token != ";"):
                    token, cls = getToken(cls)
                if (acc_name in instances.keys()):
                    error("Redefinicia instancie", 4)
                instances[acc_name] = [acc_type, "defined",
                                       virtual, privacy, static, className]
                token, cls = getToken(cls)
                continue
            if (token != "("):
                error("I dont know the input character "+token+" "+cls, 4)
            # function declaration/definition
            # read arguments
            # token, cls = getToken(cls)
            f_arg_types = ()
            f_arg_names = ()
            cls, f_arg_names, f_arg_types = getFArgs(cls)
            token, cls = getToken(cls)
            if (token == ";"):  # method declaration
                if ((acc_name, f_arg_types) in methods.keys()):
                    error("Redeklaracia metody", 4)
                methods[acc_name, f_arg_types] = [acc_type, f_arg_names, "declared", virtual,
                                                  False, privacy, static, className]
                token, cls = getToken(cls)
                continue
            if (token == "="):  # pure virtual
                token, cls = getToken(cls)  # 0 no control
                token, cls = getToken(cls)  # no control
                if ((acc_name, f_arg_types) in methods.keys()):
                    error("Redeklaracia metody", 4)
                methods[acc_name, f_arg_types] = [acc_type, f_arg_names, "declared", virtual,
                                                  True, privacy, static, className]
                token, cls = getToken(cls)
                continue
            if (token != "{"):
                error("I dont know the input character1 "+token+" "+cls, 4)
            token, cls = getToken(cls)  # }
            if ((acc_name, f_arg_types) in methods.keys()):
                error("Redefinicia metody", 4)
            methods[acc_name, f_arg_types] = [acc_type, f_arg_names, "defined", virtual,
                                              False, privacy, static, className]
            token, cls = getToken(cls)  # ;
            if (token == ";"):
                token, cls = getToken(cls)  # }
        token, cls = getToken(cls)  # ; or another class
        if (className in classes.keys()):  # uz mame danu triedu vnutri
            if (classes[className] == "declared"):
                classes[className] = [parents, methods, instances, [{}, usingM, usingI]]
            else:
                error("redefinicia triedy", 4)
        else:
            classes[className] = [parents, methods, instances, [{}, usingM, usingI]]

    return classes


def editMethod(fromP, m_t, m, to, toWho, conflicts):
    """edit function in relation to the context.

    fromP - base class + privacy
    m_t - method name
    m - method we want to add
    to - all methods that are already in
    toWho - name of claas to which we want to add
    @return: (true ,method) or (false,..) if nothing to be done (error is called when needed)
    """
    if (m[5] == 'private' and not m[4]):  # when private, no need to do anything
        return (False, [])
    if (m_t[0] == fromP[0] or m_t[0] == '~'+fromP[0]):
        return (False, [])
    if m_t not in to.keys() and m_t not in conflicts.keys():
        if (m[4]):  # pure virtual
            return (True, [m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7]])
        elif (fromP[1] == 'private'):
            return (True, [m[0], m[1], m[2], m[3], m[4], 'private', m[6], fromP[0]])
        elif (fromP[1] == 'protected'):
            return (True, [m[0], m[1], m[2], m[3], m[4], 'protected', m[6], fromP[0]])
        else:
            return (True, [m[0], m[1], m[2], m[3], m[4], m[5], m[6], fromP[0]])
    elif m_t in conflicts.keys():
        if (m[7] == conflicts[m_t][0]):
            return (True, [m[0], m[1], m[2], m[3], m[4],
                    conflicts[m_t][1], m[6], conflicts[m_t][0]])
        else:
            return (False, [])
    else:  # already in and not specified by conflict
        if (to[m_t][7] == toWho or m[4]):
            return (False, [])
        else:
            error("Conflict on method "+m_t[0], 21)


def editInstance(fromP, i_t, i, to, toWho, conflicts):
    """edit instance in relation to the context.

    fromP - base class + privacy
    i_t - instnace name
    i - instance we want to add
    to - all instances that are already in
    toWho - name of claas to which we want to add
    @return: (true ,method) or (false,..) if nothing to be done (error is called when needed)
    """
    # [2] = instances((Name), type, defined/declared, virtual, privacy,static,from)
    if (i[3] == 'private'):  # when private, no need to do anything
        return (False, [])
    if i_t not in to.keys() and i_t not in conflicts.keys():
        if (fromP[1] == 'private'):
            return (True, [i[0], i[1], i[2], 'private', i[4], fromP[0]])
        elif (fromP[1] == 'protected'):
            return (True, [i[0], i[1], i[2], 'protected', i[4], fromP[0]])
        else:
            return (True, [i[0], i[1], i[2], i[3], i[4], fromP[0]])
    elif i_t in conflicts.keys():
        if (i[5] == conflicts[i_t][0]):
            return (True, [i[0], i[1], i[2], conflicts[i_t][1], i[4], conflicts[i_t][0]])
        else:
            return (False, [])
    else:  # already in
        if (i[5] == toWho):
            return (False, [])
        else:
            error("Conflict on instance "+i_t, 21)


def makeClassesComplete(cs):
    """Fill inhereted classes methods and instances.

    cs: output from parseClasses
    """
    opened = []  # classes, that needs to be solved
    closed = []  # classes, that are solved solved
    for key in cs.keys():
        if (cs[key][0] == {}):  # no parents
            closed.append(key)
            continue
        else:
            opened.append(key)
    while (opened != []):
        for item in opened:
            if (not[e for e in cs[item][0].keys() if e not in closed]):
                for par in cs[item][0].keys():
                    # spracuj metody
                    for mt in cs[par][1].keys():
                        toDo, newM = editMethod([par, cs[item][0][par]], mt, cs[par][1][mt],
                                                cs[item][1], item, cs[item][3][1])
                        if (toDo):
                            cs[item][1][mt] = newM
                    # spracuj instancie
                    for ins in cs[par][2].keys():
                        toDo, newI = editInstance([par, cs[item][0][par]], ins, cs[par][2][ins],
                                                  cs[item][2], item, cs[item][3][2])
                        if (toDo):
                            cs[item][2][ins] = newI
                # add to solved classes (closed)
                closed.append(item)
                # remove from opened
                opened.remove(item)
    return cs


def getXMLHierarchy(acc, cs, top):
    """Return class hierarchy in XML.

    acc - class, that is now being examined
    cs - all classes
    top - the parent element
    """
    abstract = [c for c in cs[acc][1].keys() if cs[acc][1][c][4]]
    kind = 'abstract' if (abstract) else 'concrete'
    child = SubElement(top, 'class', {'kind': kind, 'name': acc})
    chls = [c for c in cs.keys() if acc in cs[c][0].keys()]
    if (chls):
        for cl in chls:
            getXMLHierarchy(cl, cs, child)


def makeXMLInstance(name, atts, top, fromWho):
    """Create XML for one instance.

    name - name of instance
    atts - attributes of instance
    top - parent element
    fromm - name of class in which this instance is located
    """
    stat = 'static' if (atts[4]) else 'instance'
    i = SubElement(top, 'attribute', {'name': name, 'type': atts[0], 'scope': stat})
    if (atts[5] != fromWho[0]):
        SubElement(i, 'from', {'name': atts[5]})


def makeXMLMethod(name, atts, top, fromWho):
    """Create XML for one method.

    name - name of method
    atts - attributes of method
    top - parent element
    fromm - name of class in which this method is located
    """
    if (atts[6]):
        stat = 'static'
    else:
        stat = 'instance'
    m = SubElement(top, 'method', {'name': name[0], 'type': atts[0], 'scope': stat})
    if (atts[7] != fromWho[0]):
        SubElement(m, 'from', {'name': atts[7]})
    if (atts[3] or atts[4]):
        if atts[4]:
            pure = 'yes'
        else:
            pure = 'no'
        SubElement(m, 'virtual', {'pure': pure})
    args = SubElement(m, 'arguments')
    for arg in range(len(name[1])):
        SubElement(args, 'argument', {'name': atts[1][arg], 'type': name[1][arg]})


def getXMLClassDetails(name, atts, t):
    """Create a xml detail of one class.

    name - name of className
    atts - all attributes of class (output from makeClassComplete or parseClasses)
    t - if not false, put new class on that
    @return - element of class acc
    """
    abstract = [c for c in atts[1].keys() if atts[1][c][4]]
    if (abstract):
        kind = 'abstract'
    else:
        kind = 'concrete'
    if (t is not False):
        top = SubElement(t, 'class', {'name': name, 'kind': kind})
    else:
        top = Element('class', {'name': name, 'kind': kind})

    # Inheritance
    if (atts[0]):
        inheritance = SubElement(top, 'inheritance')
        for base in atts[0].keys():
            SubElement(inheritance, 'from', {'name': base, 'privacy': atts[0][base]})

    # find all:
    private_m = [c for c in atts[1].keys() if atts[1][c][5] == 'private']
    public_m = [c for c in atts[1].keys() if atts[1][c][5] == 'public']
    protected_m = [c for c in atts[1].keys() if atts[1][c][5] == 'protected']

    private_i = [c for c in atts[2].keys() if atts[2][c][3] == 'private']
    public_i = [c for c in atts[2].keys() if atts[2][c][3] == 'public']
    protected_i = [c for c in atts[2].keys() if atts[2][c][3] == 'protected']

    if (private_m or private_i):
        private = SubElement(top, 'private')
    if (public_m or public_i):
        public = SubElement(top, 'public')
    if (protected_m or protected_i):
        protected = SubElement(top, 'protected')

    if (private_m):
        priv_m = SubElement(private, 'methods')
        for m in private_m:
            makeXMLMethod(m, atts[1][m], priv_m, name)

    if (public_m):
        publ_m = SubElement(public, 'methods')
        for m in public_m:
            makeXMLMethod(m, atts[1][m], publ_m, name)

    if (protected_m):
        prot_m = SubElement(protected, 'methods')
        for m in protected_m:
            makeXMLMethod(m, atts[1][m], prot_m, name)

    if (private_i):
        priv_i = SubElement(private, 'attributes')
        for i in private_i:
            makeXMLInstance(i, atts[2][i], priv_i, name)

    if (public_i):
        publ_i = SubElement(public, 'attributes')
        for i in public_i:
            makeXMLInstance(i, atts[2][i], publ_i, name)

    if (protected_i):
        prot_i = SubElement(protected, 'attributes')
        for i in protected_i:
            makeXMLInstance(i, atts[2][i], prot_i, name)
    return top


def main():
    """Main."""
    parsed = parseCommandLine(sys.argv[1:])
    keys = parsed.keys()
    if ("help" in keys):
        if (len(keys) != 1):
            error("Kombinovat --help a ine argumenty sa nepatri", 1)
        help()
    if ("input" not in keys):
        inputStream = sys.stdin
    else:
        try:
            inputStream = open(parsed["input"], "r")
        except:
            error("Input file is not valid or readable", 2)
    inputContent = inputStream.read()
    parsedClasses = parseClasses(inputContent)
    parsedClasses = makeClassesComplete(parsedClasses)

    if ('pretty-xml' in parsed.keys()):
        pretty = 4 if not parsed['pretty-xml'] else int(parsed['pretty-xml'])
    else:
        pretty = 4

    if ('details' not in parsed.keys()):
        top = Element('model')
        base = [c for c in parsedClasses.keys() if parsedClasses[c][0] == {}]
        for b in base:
            getXMLHierarchy(b, parsedClasses, top)
    else:
        if (parsed['details']):
            if (parsed['details'] not in parsedClasses.keys()):
                # TODO len hlavicka
                pass
            top = getXMLClassDetails(parsed['details'], parsedClasses[parsed['details']], False)
        else:  # all the classes
            top = Element('model')
            for cl in parsedClasses.keys():
                getXMLClassDetails(cl, parsedClasses[cl], top)
        if ('search' in parsed.keys()):
            r = top.xpath(parsed['search'])
            top = Element('result')
            toWrite = ""
            if r:
                for item in r:
                    if (isinstance(item, str)):
                        toWrite += "\n" + pretty * " " + item
                    else:
                        top.append(item)
                top.text = toWrite+"\n"
    final = prettify(top, pretty)
    if ("output" not in keys):
        outputStream = sys.stdout
    else:
        try:
            outputStream = open(parsed["output"], "w")
        except:
            error("Output file is not valid or writable", 3)
    outputStream.write(final)
main()
