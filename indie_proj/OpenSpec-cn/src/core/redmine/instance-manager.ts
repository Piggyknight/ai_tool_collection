/**
 * Redmine Instance Manager
 *
 * Manages multiple Redmine instances and auto-detects the correct instance
 * based on the current git worktree path.
 */

import path from 'path';
import { promises as fs } from 'fs';
import yaml from 'yaml';
import { RedmineConfig, RedmineCliWrapper } from './cli-wrapper.js';

export interface RedmineInstance {
  name: string;              // Instance name (e.g., "dev", "staging", "production")
  server: string;            // Redmine server URL
  apiKey: string;            // API key
  projectId: number;         // Project ID
  cliPath?: string;          // Path to red-cli.exe
  gitWorktree?: string;      // Associated git worktree path (Windows path)
}

export interface GlobalRedmineConfig {
  enabled: boolean;
  instances: RedmineInstance[];
  activeInstance?: string;  // 'auto' or instance name
}

/**
 * Configuration file locations
 */
const GLOBAL_CONFIG_PATH = path.join(process.env.USERPROFILE || '~', '.openspec', 'config.yaml');
const PROJECT_CONFIG_FILE = 'openspec/config.yaml';

export class RedmineInstanceManager {
  private instances: RedmineInstance[];
  private activeInstance: string;
  private globalConfigPath: string;

  constructor(globalConfigPath: string = GLOBAL_CONFIG_PATH) {
    this.globalConfigPath = globalConfigPath;
    this.instances = [];
    this.activeInstance = 'auto';
  }

  /**
   * Load configuration from global config file
   */
  async loadConfig(): Promise<void> {
    try {
      const configContent = await fs.readFile(this.globalConfigPath, 'utf-8');
      const config = yaml.parse(configContent);

      if (config.redmine) {
        this.instances = config.redmine.instances || [];
        this.activeInstance = config.redmine['active-instance'] || 'auto';
      }
    } catch (error) {
      // Config doesn't exist or is invalid
      this.instances = [];
      this.activeInstance = 'auto';
    }
  }

  /**
   * Save configuration to global config file
   */
  async saveConfig(): Promise<void> {
    const configDir = path.dirname(this.globalConfigPath);
    await fs.mkdir(configDir, { recursive: true });

    const configContent = yaml.stringify({
      redmine: {
        enabled: true,
        instances: this.instances,
        'active-instance': this.activeInstance,
      }
    });

    await fs.writeFile(this.globalConfigPath, configContent, 'utf-8');
  }

  /**
   * Detect the current Redmine instance based on git worktree path
   * Uses exact path matching for Windows
   */
  async detectInstance(currentPath?: string): Promise<RedmineInstance | null> {
    await this.loadConfig();

    if (this.instances.length === 0) {
      return null;
    }

    // If active instance is set to a specific name, use that
    if (this.activeInstance !== 'auto') {
      const instance = this.instances.find(i => i.name === this.activeInstance);
      return instance || null;
    }

    // Auto-detect based on git worktree path
    const worktreePath = currentPath || process.cwd();
    const normalizedPath = path.normalize(worktreePath).toLowerCase();

    // Exact path match
    const instance = this.instances.find(
      i => i.gitWorktree && path.normalize(i.gitWorktree).toLowerCase() === normalizedPath
    );

    return instance || null;
  }

  /**
   * Get a specific instance by name
   */
  getInstanceByName(name: string): RedmineInstance | undefined {
    return this.instances.find(i => i.name === name);
  }

  /**
   * List all configured instances
   */
  listInstances(): RedmineInstance[] {
    return [...this.instances];
  }

  /**
   * Register a new Redmine instance
   */
  async registerInstance(instance: RedmineInstance): Promise<void> {
    await this.loadConfig();

    // Check if instance with same name exists
    const existingIndex = this.instances.findIndex(i => i.name === instance.name);
    if (existingIndex >= 0) {
      this.instances[existingIndex] = instance;
    } else {
      this.instances.push(instance);
    }

    await this.saveConfig();
  }

  /**
   * Remove a Redmine instance
   */
  async removeInstance(name: string): Promise<void> {
    await this.loadConfig();

    this.instances = this.instances.filter(i => i.name !== name);

    await this.saveConfig();
  }

  /**
   * Set the active instance (or 'auto')
   */
  async setActiveInstance(name: string): Promise<void> {
    if (name !== 'auto' && !this.getInstanceByName(name)) {
      throw new Error(`Instance '${name}' not found`);
    }

    this.activeInstance = name;
    await this.saveConfig();
  }

  /**
   * Get the active instance name
   */
  getActiveInstanceName(): string {
    return this.activeInstance;
  }

  /**
   * Create a RedmineCliWrapper for the detected instance
   */
  async createWrapper(currentPath?: string): Promise<RedmineCliWrapper> {
    const instance = await this.detectInstance(currentPath);

    if (!instance) {
      throw new Error(
        'No Redmine instance configured for the current worktree. ' +
        'Use `openspec redmine setup` to configure an instance.'
      );
    }

    const config: RedmineConfig = {
      server: instance.server,
      apiKey: instance.apiKey,
      projectId: instance.projectId,
      cliPath: instance.cliPath
    };

    return new RedmineCliWrapper(config);
  }

  /**
   * Check if Redmine integration is enabled
   */
  async isEnabled(): Promise<boolean> {
    await this.loadConfig();
    return this.instances.length > 0;
  }

  /**
   * Get project-level Redmine config if it exists
   */
  async getProjectConfig(projectRoot: string): Promise<Partial<RedmineConfig> | null> {
    try {
      const configPath = path.join(projectRoot, PROJECT_CONFIG_FILE);
      const content = await fs.readFile(configPath, 'utf-8');
      const config = yaml.parse(content);

      if (config.redmine) {
        return {
          projectId: config.redmine['project-id'],
          cliPath: config.redmine['cli-path'],
          // Server and API key come from global config for security
        };
      }
    } catch {
      // Project config doesn't exist
    }

    return null;
  }

  /**
   * Validate instance configuration
   */
  async validateInstance(instance: RedmineInstance): Promise<boolean> {
    try {
      const wrapper = new RedmineCliWrapper({
        server: instance.server,
        apiKey: instance.apiKey,
        projectId: instance.projectId,
        cliPath: instance.cliPath
      });

      return await wrapper.testConnection();
    } catch {
      return false;
    }
  }

  /**
   * Get all instance names
   */
  getInstanceNames(): string[] {
    return this.instances.map(i => i.name);
  }
}

/**
 * Singleton instance manager
 */
let defaultManager: RedmineInstanceManager | null = null;

export function getInstanceManager(): RedmineInstanceManager {
  if (!defaultManager) {
    defaultManager = new RedmineInstanceManager();
  }
  return defaultManager;
}

export function resetInstanceManager(): void {
  defaultManager = null;
}

/**
 * Helper to get the current Redmine instance
 */
export async function getCurrentInstance(): Promise<RedmineInstance | null> {
  const manager = getInstanceManager();
  return await manager.detectInstance();
}

/**
 * Helper to get a wrapper for the current instance
 */
export async function getCurrentWrapper(): Promise<RedmineCliWrapper> {
  const manager = getInstanceManager();
  return await manager.createWrapper();
}