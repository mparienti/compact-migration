#!/usr/bin/env python3

import sys
from re import sub
from re import I as reicase
from re import compile as recompile

class MiniOptimizer:
    statements = []

    alters = []
    merge_alters = []
    creates = []
    drop_index = []
    modify_rows = []
    drops = []
    views = []
    comments = []

    alter_per_table = {}
    inter_modify = ', '

    def __init__(self, readable_statement = False):
        self.re_index = recompile('.*index[ ]*\([ ]*`(\w+)`[ ]*\).*', reicase)
        if readable_statement:
            self.inter_modify = ", \n    "

    # Read file name from command line and fill statements variables
    def read_files(self, files):
        for f in files:
            with open(f) as file:
                for line in file:
                    line = line.strip()
                    if (line == ""): # no empty lines
                        continue
                    self.statements.append(line)

    def sort_statements(self):
        for s in self.statements:
            words = s.split()
            first_word = words[0].lower()
            if first_word == "alter":
                if words[1].lower() == "table":
                    self.alters.append(self.remove_isam(s))
                else:
                    raise(Exception("Find a curious ALTER statements:\n" + s ))
            elif first_word == "create":
                if words[1].lower() == "table":
                    self.creates.append(s)
                elif len(words) > 7 and ' '.join(words[0:7]).lower() == "create or replace sql security invoker view":
                    self.views.append(s)
                else:
                    raise(Exception("Find a curious CREATE statements:\n" + s ))
            elif first_word == "insert" or first_word == "update" or first_word == "delete" or first_word == "replace":
                self.modify_rows.append(s)
            elif first_word == "drop":
                if words[1].lower() == "table":
                    self.drops.append(s)
                elif words[1].lower() == "index":
                    self.drop_index.append(s)
                else:
                    raise(Exception("Find a curious DROP statements:\n" + s ))
            elif first_word[0] == "#" or first_word[0:2] == "--":
                self.comments.append(s)
            else:
                raise(Exception("Do know how to manage this statements:\n" + s))

    def group_alters(self):
        for alter in self.alters:
            table_name = alter.split()[2]
            if "`" not in table_name:
                table_name = "`" + table_name +  "`"
            if not table_name in self.alter_per_table.keys():
                self.alter_per_table[table_name] = []
            self.alter_per_table[table_name].append(alter)

    def join_alters(self):
        if len(self.alter_per_table) == 0:
            self.group_alters()
        for table_name in self.alter_per_table.keys():
            # copy alters statements in reverse order to have last first
            alters = self.alter_per_table[table_name][::-1]
            already_in = {} # dict: field_name => sql_statement
            sql = []
            sql.append(self.clean_eol(alters[0]))
            already_in[self.get_field(sql[0])] = 0
            for s in alters[1:]:
                field = self.get_field(s)
                if field not in ['`KEY`', '`PRIMARY`'] and field in already_in.keys(): ### and 'index_' not in field?
                    # the field modified has already been inserted
                    if s.split()[3] == "ADD" and s.split()[3] == "ADD":
                        sql[already_in[field]] = sql[already_in[field]].replace("CHANGE " + field, "ADD")
                    continue
                already_in[field] = len(already_in)
                # remove 3 words at the beginning of the line (alter table table_name)
                s = ' ' . join(s.split()[3:])
                sql.append( self.clean_eol(s))
            self.merge_alters.append(self.inter_modify.join(sql) + ';')

    def get_field(self, alter_stmt):
        alter_stmt_token = alter_stmt.split()
        field_name = alter_stmt_token[4]
        if field_name == "COLUMN":
            field_name = alter_stmt_token[5]
        if "`" not in field_name:
            field_name = "`" + field_name +  "`"
        if '=' in field_name:
            field_name = field_name.split('=')[0]
        match_index = self.re_index.match(alter_stmt)
        if match_index:
            field_name = 'index_' + match_index.group(1)
        elif field_name.lower() == '`index`':
            field_name = 'index_' + alter_stmt_token[5]
        if field_name[-1] == ';':
            field_name = field_name[:-1]
        #print (field_name)
        return field_name

    def remove_isam(self, string):
        return sub(r'engine[ ]*=[ ]*myisam', '', string, flags=reicase)

    def clean_eol(self, string):
        string = string.strip()
        if (string[-1] == ';'):
            return string[:-1]
        pos_comment = string.rfind('#')
        if (pos_comment == -1):
            raise (Exception("Alter table statement without ';' and without comment:\n" + s))
        return self.clean_eol(string[:pos_comment])

    def work(self):
        self.sort_statements()
        self.group_alters()
        self.join_alters()

    def dump_all(self):
        for stat in (self.drops, self.creates, self.drop_index, self.merge_alters, self.modify_rows, self.views):
        #for stat in (self.merge_alters, []): #when testin
            for line in stat:
                print(line)


files = sys.argv[1:]

if (len(files) == 0):
    print("This program waits for file names as input")
    sys.exit()

optimizer = MiniOptimizer(True)# Instanciate this class without True argument
                               # if you want each ALTER TABLE statement on exactly one line
optimizer.read_files(files)

optimizer.sort_statements()
optimizer.group_alters()
optimizer.join_alters()


optimizer.dump_all()



# Filter each statements into: update, drop, modify_rows, comment
