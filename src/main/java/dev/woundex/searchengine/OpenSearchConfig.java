package dev.woundex.searchengine;

import org.apache.http.HttpHost;
import org.opensearch.client.RestClient;
import org.opensearch.client.opensearch.OpenSearchClient;
import org.opensearch.client.transport.rest_client.RestClientTransport;
import org.opensearch.client.json.jackson.JacksonJsonpMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenSearchConfig {

    @org.springframework.beans.factory.annotation.Value("${opensearch.host:localhost}")
    private String openSearchHost;

    @org.springframework.beans.factory.annotation.Value("${opensearch.port:9200}")
    private int openSearchPort;

    @Bean
    public OpenSearchClient openSearchClient() {
        RestClient restClient = RestClient.builder(
                new HttpHost(openSearchHost, openSearchPort, "http")
        ).build();

        RestClientTransport transport = new RestClientTransport(
                restClient, new JacksonJsonpMapper()
        );

        return new OpenSearchClient(transport);
    }
}
