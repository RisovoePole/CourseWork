package import_data;

import entities.Faculty;
import entities.Specialization;
import com.opencsv.CSVParserBuilder;
import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import com.opencsv.exceptions.CsvValidationException;

import java.io.*;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.Vector;

public class Importer {
    public Importer(){};

    private Path path = Paths.get(System.getProperty("user.dir"), "src", "Files");
    private Character separator =',';

    public Path getPath() {
        return path;
    }

    public Character getSeparator() {
        return separator;
    }

    public void setPath(Path path) {
        this.path = path;
    }

    public void setSeparator(Character separator) {
        this.separator = separator;
    }

    private Integer[] findCorrespondIndexes(String[] headersFromCSV, String[] correctHeaders) throws ImportException {
        int rightHeadersLength = correctHeaders.length;
        Integer[] result = new Integer[rightHeadersLength];
        Map<String, Integer> headerIndexes = new HashMap<>();
        for(int idx = 0; idx<headersFromCSV.length; idx++){
            headerIndexes.put(headersFromCSV[idx].toLowerCase(), idx);
        }

        Vector<String> missingColumns = new Vector<>();

        for(int i=0; i<rightHeadersLength; i++){
            Integer index = headerIndexes.get(correctHeaders[i].toLowerCase());
            if(index == null) missingColumns.add(correctHeaders[i]);
            result[i] = index;
        }

        if(!missingColumns.isEmpty()) {
            StringBuilder errorMsg = new StringBuilder("ERROR: No column(s): ");
            errorMsg.append(String.join(", ", missingColumns));
            throw new ImportException(errorMsg.toString());
        }
        return result;
    }

    public Vector<Faculty> importFaculties(Path csvFilePath) throws ImportException, CsvValidationException, IOException {
        CSVReader reader = new CSVReaderBuilder(new FileReader(csvFilePath.toFile()))
                .withCSVParser(new CSVParserBuilder()
                        .withSeparator(separator)
                        .build())
                .build();

        String[] columnsNames = {"faculty name"};
        Integer[] rightIdx = new Integer[columnsNames.length];

        String[] nextLine, headers;
        if ((nextLine = reader.readNext()) != null) {
            headers = nextLine;
            rightIdx = findCorrespondIndexes(headers, columnsNames);
        } else {
            System.out.println("CSV file is empty");
            return null;
        }

        Vector<Faculty> facultyList = new Vector<>();

        while ((nextLine = reader.readNext()) != null) {
            if(nextLine.length < headers.length) throw new ImportException("Not enough data on line " + reader.getLinesRead());
            String name = nextLine[rightIdx[0]];
            facultyList.add(new Faculty(null, name));
        }

        reader.close();
        return facultyList;
    }


    public Vector<Specialization> importSpecsForFaculty(Path csvFilePath, Integer facultyId) throws ImportException, CsvValidationException, IOException {
        CSVReader reader = new CSVReaderBuilder(new FileReader(csvFilePath.toFile()))
                .withCSVParser(new CSVParserBuilder()
                        .withSeparator(separator)
                        .build())
                .build();

        String[] columnsNames = {"Specialization name", "years of study"};
        Integer[] rightIdx = new Integer[columnsNames.length];

        String[] nextLine, headers;
        if ((nextLine = reader.readNext()) != null) {
            headers = nextLine;
            rightIdx = findCorrespondIndexes(headers, columnsNames);
        } else {
            System.out.println("CSV file is empty");
            return null;
        }

        Vector<Specialization> SpecsList = new Vector<>();

        while ((nextLine = reader.readNext()) != null) {
            String spec_name = nextLine[rightIdx[0]];
            String year_of_studyS = nextLine[rightIdx[1]];
            int year_of_study = 0;
            try{
                year_of_study = Integer.parseInt(year_of_studyS);
            } catch (NumberFormatException e) {
                throw new ImportException("Value \"years of study\" of specialization \t"+spec_name+" is not a number - \""+year_of_studyS+"\"" );
            }
            SpecsList.add(new Specialization(null, spec_name, facultyId,year_of_study));
        }

        reader.close();
        return SpecsList;
    }

}
