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
        } catch (Exception e) {
            // Return empty results gracefully when index is not found or error occurs
            return results;
        }
        return results;
    }

    @GetMapping("/suggest")
    public List<String> suggest(@RequestParam String q) {
        List<String> suggestions = new ArrayList<>();
        if (q == null || q.trim().isEmpty()) {
            return suggestions;
        }

        try {
            SearchResponse<Map> searchResponse = openSearchClient.search(s -> s
                            .index(INDEX_NAME)
                            .size(10)
                            .query(q1 -> q1
                                    .multiMatch(m -> m
                                            .query(q.trim())
                                            .fields("title^3", "headings^2", "content")
                                            .type(org.opensearch.client.opensearch._types.query_dsl.TextQueryType.PhrasePrefix)
                                    )
                            ),
                    Map.class
            );

            java.util.Set<String> uniqueSuggestions = new java.util.LinkedHashSet<>();
            for (Hit<Map> hit : searchResponse.hits().hits()) {
                Map source = hit.source();
                if (source != null) {
                    Object titleObj = source.get("title");
                    if (titleObj != null) {
                        String titleStr = titleObj.toString().trim();
                        if (!titleStr.isEmpty()) {
                            uniqueSuggestions.add(titleStr);
                        }
                    }
                    Object headingsObj = source.get("headings");
                    if (headingsObj instanceof List) {
                        for (Object h : (List<?>) headingsObj) {
                            if (h != null) {
                                String hStr = h.toString().trim();
                                if (!hStr.isEmpty()) {
                                    uniqueSuggestions.add(hStr);
                                }
                            }
                        }
                    }
                }
            }
            suggestions.addAll(uniqueSuggestions);
        } catch (Exception e) {
            // Return empty list gracefully on failure or missing index
        }
        return suggestions;
    }
}
