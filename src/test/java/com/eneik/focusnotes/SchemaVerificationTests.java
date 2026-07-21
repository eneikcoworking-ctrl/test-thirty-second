package com.eneik.focusnotes;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
public class SchemaVerificationTests {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    public void testNotesTableExistsAndHasExpectedColumns() {
        // Retrieve columns metadata from the database
        List<Map<String, Object>> columns = jdbcTemplate.queryForList(
                "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NOTES'"
        );

        assertThat(columns).isNotEmpty();

        boolean hasId = false;
        boolean hasOwner = false;
        boolean hasTitle = false;
        boolean hasBody = false;
        boolean hasCreatedAt = false;
        boolean hasUpdatedAt = false;

        for (Map<String, Object> col : columns) {
            String colName = ((String) col.get("COLUMN_NAME")).toUpperCase();
            if ("ID".equals(colName)) hasId = true;
            else if ("OWNER".equals(colName)) hasOwner = true;
            else if ("TITLE".equals(colName)) hasTitle = true;
            else if ("BODY".equals(colName)) hasBody = true;
            else if ("CREATED_AT".equals(colName)) hasCreatedAt = true;
            else if ("UPDATED_AT".equals(colName)) hasUpdatedAt = true;
        }

        assertThat(hasId).isTrue();
        assertThat(hasOwner).isTrue();
        assertThat(hasTitle).isTrue();
        assertThat(hasBody).isTrue();
        assertThat(hasCreatedAt).isTrue();
        assertThat(hasUpdatedAt).isTrue();
    }

    @Test
    public void testIndexOnOwnerAndCreatedAtDescExists() {
        // Query to check index in H2
        List<Map<String, Object>> indexes = jdbcTemplate.queryForList(
                "SELECT INDEX_NAME, COLUMN_NAME, ORDERING_SPECIFICATION " +
                "FROM INFORMATION_SCHEMA.INDEX_COLUMNS " +
                "WHERE TABLE_NAME = 'NOTES' AND INDEX_NAME = 'IDX_NOTES_OWNER_CREATED_AT_DESC' " +
                "ORDER BY ORDINAL_POSITION ASC"
        );

        assertThat(indexes).hasSize(2);

        Map<String, Object> col1 = indexes.get(0);
        assertThat(col1.get("COLUMN_NAME").toString().toUpperCase()).isEqualTo("OWNER");

        Map<String, Object> col2 = indexes.get(1);
        assertThat(col2.get("COLUMN_NAME").toString().toUpperCase()).isEqualTo("CREATED_AT");
        assertThat(col2.get("ORDERING_SPECIFICATION").toString().toUpperCase()).isEqualTo("DESC");
    }
}
