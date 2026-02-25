package org.app;

import entities.Discipline;
import entities.Faculty;
import entities.Specialization;
import entities.StudentGroup;
import entities.StudyHours;
import import_.data.ImportException;
import import_.data.Importer;
import use.db.Reader;
import use.db.Writer;
import com.opencsv.exceptions.CsvValidationException;
import io.bretty.console.table.Table;
import io.bretty.console.table.Alignment;
import io.bretty.console.table.ColumnFormatter;
import io.bretty.console.table.Precision;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Vector;
import java.sql.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;

public class App
{
    static Reader r;
    static Writer w;
    static Scanner in;
    static Importer importer;

    public static void main( String[] args ) {
        String url = "jdbc:postgresql://localhost:5432/mybd";
        String user = "victor";
        String password = "1111";
        in = new Scanner(System.in);
        Connection conn;
        try {
            conn = DriverManager.getConnection(url, user, password);
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
         r = new Reader(conn);
         w = new Writer(conn);
        importer = new Importer();
        while(true){
            Vector<Faculty> faculties = r.getFacultyList();
            System.out.println("--------------------------------------");
            if(faculties.isEmpty()){
                System.out.println("No faculties have been added.");
            }
            else{
                int i=0;
                for(Faculty f : faculties){
                    System.out.println((++i)+")"+f);
                }
            }
            System.out.println("--------------------------------------");
            System.out.println("\n\nwrite \\choose to show specializations for some faculty.");
            System.out.println("write \\add to add faculty.");
            System.out.println("write \\import to import faculties.\n");
            System.out.println("write \\exit to cancel the program.\n\n");

            String response = in.nextLine();

            switch(response){
                case "\\choose" -> {
                    if(faculties.isEmpty()) {
                        System.out.println("No faculties to choose...\n\n");
                        continue;
                    }
                    int num=0;
                    while(true) {
                        System.out.print("\ntype a number from the list(not an id):\t");
                        try{
                            String numS = in.nextLine();
                            num = Integer.parseInt(numS);
                        } catch (NumberFormatException e){
                            System.out.println("ERROR: not a number");
                            continue;
                        }
                        if(num<1 || num>faculties.size()){
                            System.out.println("Number out of bounds.");
                            continue;
                        }
                        break;
                    }
                    specsMenu(faculties.get(num-1).id());
                }
                case "\\add" -> {
                    int result=0;
                    do{
                        System.out.print("\ntype a name for faculty:\t");
                        String name = in.nextLine().trim();
                        result = w.addFaculty(name);
                    } while(result == 0);
                    System.out.println("Success!\n\n");
                }
                case "\\import" -> {
                    //вызов функции импорта - получение нужного файла - вызов нужного метода из импортера
                    Path file = ImportMenu();
                    if (file == null) continue;
                    try {
                        Vector<Faculty> importFaculties= importer.importFaculties(file);
                        if(importFaculties==null) continue;

                        int total_added =0;
                        int result=0;
                        for(Faculty f : importFaculties){
                            result = w.addFaculty(f.name());
                            if(result != 0) total_added++;
                        }

                        if(total_added!=0)
                            System.out.println("File\t"+file.getFileName().toString()+"\tsuccessfully imported!\n Total imported faculties - "+total_added);
                        else
                            System.out.println("None of faculties from file have been imported.");
                    } catch (ImportException | CsvValidationException | IOException e) {
                        System.out.println(e.getMessage());
                    }
                }
                case "\\exit"->{
                   return;
                }
            }
        }


    }

    public static void specsMenu(Integer facultyId){
        while(true){
            Vector<Specialization> specs = r.getSpecsByFaculty(facultyId);
            System.out.println("--------------------------------------");
            if(specs.isEmpty()){
                System.out.println("No specializations have been added.");
            }
            else{
                int i=0;
                for(Specialization f : specs){
                    System.out.println((++i)+")"+f);
                }
            }
            System.out.println("--------------------------------------");
            System.out.println("\n\nwrite \\choose to show details for some specialization.");
            System.out.println("write \\add to add specialization.");
            System.out.println("write \\import to import specialization.\n");
            System.out.println("write \\back to check list of specializations");
            System.out.println("write \\exit to cancel the program.\n\n");

            String response = in.nextLine();

            switch(response){
                case "\\choose" -> {
                    if(specs.isEmpty()) {
                        System.out.println("No specializations to choose...\n\n");
                        continue;
                    }
                    int num=0;
                    while(true) {
                        System.out.print("\ntype a number from the list(not an id):\t");
                        try{
                            String numS = in.nextLine().trim();
                            num = Integer.parseInt(numS);
                        } catch (NumberFormatException e){
                            System.out.println("ERROR: not a number");
                            continue;
                        }
                        if(num<1 || num>specs.size()){
                            System.out.println("Number out of bounds.");
                            continue;
                        }
                        break;
                    }
                    GroupsAndDisciplineMenu(specs.get(num-1).id());
                }
                case "\\add" -> {
                    int result = 0;
                    do{
                        System.out.print("\ntype a name for specialization:\t");
                        String name = in.nextLine().trim();
                        System.out.print("\ntype years of study:\t");
                        String yearsOfStudyS = in.nextLine().trim();
                        int yearsOfStudy=0;
                        try {
                            yearsOfStudy = Integer.parseInt(yearsOfStudyS);
                        } catch (NumberFormatException e){
                            System.out.println("ERROR: not a number");
                            continue;
                        }
                        if(yearsOfStudy<1){
                            System.out.println("Number out of bounds.");
                            continue;
                        }
                        result = w.addSpec(name, facultyId, yearsOfStudy);
                    } while(result == 0);
                    System.out.println("Success!\n\n");
                }

                case "\\import" -> {
                    //вызов функции импорта - получение нужного файла - вызов нужного метода из импортера
                    Path file = ImportMenu();
                    if (file == null) continue;
                    try {
                        Vector<Specialization> importSpecializations = importer.importSpecsForFaculty(file, facultyId);
                        if(importSpecializations == null) continue;

                        int total_added =0;
                        int result=0;
                        for(Specialization spec : importSpecializations){
                            result = w.addSpec(spec.name(), spec.faculty_id(), spec.yearsOfStudy());
                            if(result != 0) total_added++;
                        }

                        if(total_added!=0)
                            System.out.println("File\t"+file.getFileName().toString()+"\tsuccessfully imported!\n Total imported specializations - "+total_added);
                        else
                            System.out.println("None of specializations from file have been imported.");
                    } catch (ImportException | CsvValidationException | IOException e) {
                        System.out.println(e.getMessage());
                    }
                }
                case "\\back" ->{
                    return;
                }
                case "\\exit" ->{
                    System.exit(0);
                }
            }
        }
    }

    public static void GroupsAndDisciplineMenu(Integer specId){
        while(true){
            Vector<Discipline> disciplines = r.getDisciplinesBySpec(specId);

            Vector<StudentGroup> groups = r.getGroupsBySpec(specId);
            System.out.println("--------------------------------------");
            if(disciplines.isEmpty()){
                System.out.println("No disciplines have been added.");
            }
            else{
                String[] header = {"Discipline","Study semester", "Total hours", "Contact hours", "Independent hours","Course hours","Seminar hours", "Laboratories hours", "Credits"};


                int n = disciplines.size();

                // Колонки таблицы
                String[]  colDiscipline   = new String[n];
                Integer[] colSemester     = new Integer[n];
                Float[]   colContact      = new Float[n];
                Float[]   colIndependent  = new Float[n];
                Float[]   colCourse       = new Float[n];
                Float[]   colSeminar      = new Float[n];
                Float[]   colLaboratories = new Float[n];
                Float[]   colTotal        = new Float[n];
                Float[]   colCredits      = new Float[n];

                for (int i = 0; i < n; i++) {
                    Discipline d = disciplines.get(i);
                    StudyHours h = r.getStudyHoursByDiscipline(d.id());

                    float contact      = h != null && h.contactStudyHours()      != null ? h.contactStudyHours()      : 0f;
                    float independent  = h != null && h.independentStudyHours()  != null ? h.independentStudyHours()  : 0f;
                    float course       = h != null && h.courseHours()            != null ? h.courseHours()            : 0f;
                    float seminar      = h != null && h.seminarHours()           != null ? h.seminarHours()           : 0f;
                    float laboratories = h != null && h.laboratoriesHours()      != null ? h.laboratoriesHours()      : 0f;

                    float total = contact + independent;

                    colDiscipline[i]   = d.name();
                    colSemester[i]     = d.studySemester();
                    colContact[i]      = contact;
                    colIndependent[i]  = independent;
                    colCourse[i]       = course;
                    colSeminar[i]      = seminar;
                    colLaboratories[i] = laboratories;
                    colTotal[i]        = total;
                    colCredits[i]      = d.credits();
                }

                // Форматирование колонок
                ColumnFormatter<String> disciplineFmt =
                        ColumnFormatter.text(Alignment.LEFT, 25);              // название подлиннее

                ColumnFormatter<Number> semesterFmt   =
                        ColumnFormatter.number(Alignment.CENTER, 14, Precision.ZERO);

                ColumnFormatter<Number> hoursFmt      =
                        ColumnFormatter.number(Alignment.CENTER, 18, Precision.ONE); // часы с одним знаком после запятой

                ColumnFormatter<Number> creditsFmt    =
                        ColumnFormatter.number(Alignment.CENTER, 8, Precision.ONE);

                // Собираем таблицу по колонкам
                Table.Builder builder = new Table.Builder(header[0], colDiscipline, disciplineFmt);

                builder.addColumn(header[1], colSemester,     semesterFmt);
                builder.addColumn(header[2], colTotal,        hoursFmt);
                builder.addColumn(header[3], colContact,      hoursFmt);
                builder.addColumn(header[4], colIndependent,  hoursFmt);
                builder.addColumn(header[5], colCourse,       hoursFmt);
                builder.addColumn(header[6], colSeminar,      hoursFmt);
                builder.addColumn(header[7], colLaboratories, hoursFmt);
                builder.addColumn(header[8], colCredits,      creditsFmt);

                Table disciplineTable = builder.build();

                System.out.println();
                System.out.println(disciplineTable);

            }
            System.out.println("\n==========");
            if(groups.isEmpty()){
                System.out.println("No groups have been added.");
            }
            else{
                for(StudentGroup g : groups){
                    System.out.println("- "+g);
                }
            }
            System.out.println("--------------------------------------");
            System.out.println("write \"\\add g\" to add a group.");
            System.out.println("write \"\\add d\" to add a discipline.\n");
            System.out.println("write \\back to check list of specializations");
            System.out.println("write \\exit to cancel the program.\n\n");

            String response = in.nextLine();

            switch(response){
                case "\\add d" -> {
                    int result = 0;
                    do{
                        System.out.print("\ntype a name for discipline:\t");
                        String name = in.nextLine().trim();
                        System.out.print("\ntype study semester:\t");
                        String studySemesterS = in.nextLine().trim();
                        System.out.print("\ntype credits:\t");
                        String creditsS = in.nextLine().trim();
                        int studySemester =0;
                        float credits=0;
                        try {
                            studySemester = Integer.parseInt(studySemesterS);
                            credits = Float.parseFloat(creditsS);
                        } catch (NumberFormatException e){
                            System.out.println("ERROR: not a number");
                            continue;
                        }
                        if(studySemester <1 || credits<1){
                            System.out.println("Number out of bounds.");
                            continue;
                        }
                        result = w.addDiscipline(specId, name, studySemester, credits);
                    } while(result == 0);
                    System.out.println("Success! Discipline was added. \n Enter more details:");
                    int generatedKey = result;
                    result =0;
                    do{
                        float contactStudyHours, independentStudyHours, courseHours, seminarHours, laboratoriesHours;

                        System.out.print("\ntype contact study hours:\t");
                        String contactStudyHoursS = in.nextLine().trim();

                        System.out.print("\ntype independent study hours:\t");
                        String independentStudyHoursS = in.nextLine().trim();

                        System.out.print("\ntype course hours:\t");
                        String courseHoursS = in.nextLine().trim();

                        System.out.print("\ntype seminar hours:\t");
                        String seminarHoursS = in.nextLine().trim();

                        System.out.print("\ntype laboratory hours:\t");
                        String laboratoriesHoursS = in.nextLine().trim();

                        try{
                            contactStudyHours = Float.parseFloat(contactStudyHoursS);
                            independentStudyHours = Float.parseFloat(independentStudyHoursS);
                            courseHours = Float.parseFloat(courseHoursS);
                            seminarHours = Float.parseFloat(seminarHoursS);
                            laboratoriesHours = Float.parseFloat(laboratoriesHoursS);
                        } catch (NumberFormatException e) {
                            System.out.println("ERROR: not a number");
                            continue;
                        }
                        if(contactStudyHours <0 || independentStudyHours<0|| courseHours<0|| seminarHours<0|| laboratoriesHours<0){
                            System.out.println("Number out of bounds.");
                            continue;
                        }
                        StudyHours st = new StudyHours(generatedKey,contactStudyHours, independentStudyHours, courseHours, seminarHours, laboratoriesHours);
                        result = w.addStudyHoursForDiscipline(st);
                    }while(result == 0);
                    System.out.println("Success!\n\n");
                }
                case "\\add g" -> {
                    int result;
                    do{
                        System.out.print("\ntype a name for group:\t");
                        String name = in.nextLine().trim();
                        result = w.addGroup(specId,name);
                    } while(result == 0);
                    System.out.println("Success!\n\n");
                }
                case "\\back" ->{
                    return;
                }
                case "\\exit" ->{
                    System.exit(0);
                }
            }
        }
    }

    public static Path ImportMenu(){

        while (true) {
            System.out.printf("""
                                Current folder: %s
                                write \\path to change folder.
                                write \\select to choose a file.
                                write \\separator to change it. Current separator: "%s" \n
                                write \\back to close this menu.
                                Support types: CSV \n""",
                    importer.getPath().toAbsolutePath(),
                    importer.getSeparator());

            String import_response = in.nextLine().trim();

            switch (import_response) {
                case "\\path" -> {

                    try (Stream<Path> stream = Files.list(importer.getPath())) {
                        System.out.println("Folders in current folder:");
                        List<Path> Directories = stream
                                .filter(p -> Files.isDirectory(p))
                                .toList();

                        if (Directories.isEmpty()) {
                            System.out.println("No subfolders in current folder.");
                        } else {
                            AtomicInteger i = new AtomicInteger(1);
                            Directories.forEach(name -> {
                                int idx = i.getAndIncrement();

                                System.out.print(name.getFileName().toString() + (idx % 5 != 0 ? '\t' : '\n'));
                            });
                        }
                    } catch (IOException e) {
                        System.out.println(e.getMessage());
                    }

                    System.out.println("\nEnter new folder path:\t");
                    String newPathStr = in.nextLine().trim();
                    Path folder;
                    Path newPath = Paths.get(newPathStr);
                    if (newPath.isAbsolute()) {
                        folder = newPath.normalize();
                    } else {
                        folder = importer.getPath().resolve(newPath).normalize();
                    }

                    if (!Files.isDirectory(folder)) {
                        System.out.println("Written path is not a directory! " + folder);
                        continue;
                    }

                    importer.setPath(folder.normalize());
                    System.out.println("Path changed successfully!");
                }
                case "\\select" -> {

                    try (Stream<Path> stream = Files.list(importer.getPath())) {
                        AtomicInteger i = new AtomicInteger(1);

                        stream
                                .map(p -> p.getFileName().toString())
                                .forEach(name -> {
                                    int idx = i.getAndIncrement();
                                    System.out.print(name + (idx % 5 != 0 ? '\t' : '\n'));
                                });

                    } catch (IOException e) {
                        System.out.println(e.getMessage());
                    }


                    System.out.println("\nEnter file name:\t");
                    String fileName = in.nextLine().trim();
                    Path file = importer.getPath().resolve(fileName);
                    if(!Files.isRegularFile(file)){
                        System.out.println("Written file name doesn't exist!");
                        continue;
                    }
                    System.out.println("File was found successfully!");
                    return file;
                }

                case "\\separator" -> {
                    System.out.println("Enter new separator (will be used first character from your input):\n");
                    String newSeparator = in.nextLine().trim();
                    if (!newSeparator.isEmpty()) {
                        System.out.println("Separator has changed!");
                        importer.setSeparator(newSeparator.charAt(0));
                    } else {
                        System.out.println("Separator didn't changed.");
                    }
                }

                case "\\back" -> {
                    return null;
                }
            }
        }
    }
}

