package dev.woundex.searchengine;

import org.opensearch.client.opensearch.OpenSearchClient;
import org.opensearch.client.opensearch.core.SearchResponse;
import org.opensearch.client.opensearch.core.search.Hit;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class SearchController {

    private final OpenSearchClient openSearchClient;
    private static final String INDEX_NAME = "enterprise-search-chunks";

    @Autowired
    public SearchController(OpenSearchClient openSearchClient) {
        this.openSearchClient = openSearchClient;
    }

    @GetMapping("/search")
    public List<Map> search(@RequestParam String q) {
        List<Map> results = new ArrayList<>();
        try {
            SearchResponse<Map> searchResponse = openSearchClient.search(s -> s
                            .index(INDEX_NAME)
                            .query(q1 -> q1
                                    .multiMatch(m -> m
                                            .query(q)
                                            .fields("content", "title", "headings")
                                    )
                            ),
                    Map.class
            );

            for (Hit<Map> hit : searchResponse.hits().hits()) {
                if (hit.source() != null) {
                    results.add(hit.source());
                }
            }
        } catch (IOException e) {
            throw new RuntimeException("Error executing search", e);
        }
        return results;
    }
}
