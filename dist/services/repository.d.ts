export interface SeedResult {
    success: boolean;
    prUrl?: string;
    branchName?: string;
    error?: string;
    filesAdded?: string[];
}
export interface RepositoryStatus {
    isSeeded: boolean;
    specKitVersion?: string;
    lastSeededDate?: Date;
    configFiles?: string[];
}
export declare class RepositoryService {
    private seedAssets;
    isRepositorySeeded(projectId: string): Promise<boolean>;
    getRepositoryStatus(projectId: string): Promise<RepositoryStatus>;
    seedRepository(projectId: string, targetRepo?: string): Promise<SeedResult>;
    private getDefaultRepository;
    private createBranch;
    private addFile;
    private createPullRequest;
    private getPromptTemplate;
    private getConfigTemplate;
    saveArtifact(projectId: string, filePath: string, content: string, commitMessage: string): Promise<void>;
    getArtifacts(projectId: string, artifactType: 'specs' | 'plans' | 'tasks'): Promise<string[]>;
}
