#!/usr/bin/env python3

import sys

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
                    self.alters.append(s)
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
        # make some hard work here :-)
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
            already_in = []
            sql = self.clean_eol(alters[0])
            already_in.append(self.get_field(sql))
            for s in alters[1:]:
                field = self.get_field(s)
                if field in already_in:
                    # the field modified has already been inserted
                    continue
                already_in.append(field)
                # remove 3 words at the beginning of the line
                s = ' '.join(s.split()[3:])
                sql = sql + ', ' + self.clean_eol(s)
            self.merge_alters.append(sql+';')


    def get_field(self, alter_stmt):
        field_name = alter_stmt.split()[4]
        if "`" not in field_name:
            field_name = "`" + field_name +  "`"
        return field_name

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

optimizer = MiniOptimizer()
optimizer.read_files(files)

optimizer.sort_statements()
optimizer.group_alters()
optimizer.join_alters()


# when finish
optimizer.dump_all()



# Filter each statements into: update, drop, modify_rows, comment

# fetch table from update

# 
