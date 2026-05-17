/**
 * Status Mapping between OpenSpec and Redmine
 *
 * Maps OpenSpec workflow states to Redmine issue statuses.
 * Supports the Hermes 7-state workflow and Bug workflow.
 */

/**
 * Hermes workflow states - 7 states for Task Kanban
 */
export const HERMES_STATES = [
  'plan',
  'propose',
  'applying',
  'done',
  'code-review',
  'testing',
  'archiving'
] as const;

export type HermesState = typeof HERMES_STATES[number];

/**
 * Bug workflow states - 4 states for Bug panel
 */
export const BUG_STATES = [
  'new',
  'in-progress',
  'fixed',
  'verified'
] as const;

export type BugState = typeof BUG_STATES[number];

/**
 * Default mapping from Hermes states to Redmine status names
 * These should be configurable per Redmine instance
 */
export const DEFAULT_HERMES_STATUS_MAPPING: Record<HermesState, string> = {
  'plan': 'Plan',
  'propose': 'Propose',
  'applying': 'Applying',
  'done': 'Done',
  'code-review': 'Code Review',
  'testing': 'Testing',
  'archiving': 'Archiving'
};

/**
 * Default mapping from Bug states to Redmine status names
 */
export const DEFAULT_BUG_STATUS_MAPPING: Record<BugState, string> = {
  'new': '待修复',
  'in-progress': '修复中',
  'fixed': '修复完成',
  'verified': '验证完成'
};

/**
 * Default mapping for OpenSpec's original workflow to Hermes workflow
 */
export const OPENSPEC_TO_HERMES_MAPPING: Record<string, HermesState> = {
  'proposal': 'plan',
  'specs': 'propose',
  'design': 'propose',
  'tasks': 'applying',
  'apply': 'applying',
  'archive': 'archiving'
};

/**
 * Configurable status mappings
 * These are loaded from project config
 */
export interface ConfigurableStatusMappings {
  hermes?: Partial<Record<HermesState, string>>;
  bug?: Partial<Record<BugState, string>>;
  custom?: Record<string, string>;
}

export class StatusMapper {
  private hermesMapping: Record<HermesState, string>;
  private bugMapping: Record<BugState, string>;
  private customMapping: Record<string, string>;

  constructor(config?: ConfigurableStatusMappings) {
    // Merge defaults with config
    this.hermesMapping = {
      ...DEFAULT_HERMES_STATUS_MAPPING,
      ...(config?.hermes || {})
    };
    this.bugMapping = {
      ...DEFAULT_BUG_STATUS_MAPPING,
      ...(config?.bug || {})
    };
    this.customMapping = config?.custom || {};
  }

  /**
   * Map Hermes state to Redmine status name
   */
  hermesToRedmine(state: HermesState): string {
    return this.hermesMapping[state];
  }

  /**
   * Map Bug state to Redmine status name
   */
  bugToRedmine(state: BugState): string {
    return this.bugMapping[state];
  }

  /**
   * Map custom state to Redmine status name
   */
  customToRedmine(state: string): string | undefined {
    return this.customMapping[state];
  }

  /**
   * Map OpenSpec artifact state to Hermes state
   */
  openspecToHermes(artifact: string): HermesState | undefined {
    return OPENSPEC_TO_HERMES_MAPPING[artifact];
  }

  /**
   * Get all Hermes states
   */
  getHermesStates(): readonly HermesState[] {
    return HERMES_STATES;
  }

  /**
   * Get all Bug states
   */
  getBugStates(): readonly BugState[] {
    return BUG_STATES;
  }

  /**
   * Get next state in Hermes workflow
   */
  getNextHermesState(current: HermesState): HermesState | null {
    const index = HERMES_STATES.indexOf(current);
    if (index < HERMES_STATES.length - 1) {
      return HERMES_STATES[index + 1];
    }
    return null;
  }

  /**
   * Get previous state in Hermes workflow
   */
  getPreviousHermesState(current: HermesState): HermesState | null {
    const index = HERMES_STATES.indexOf(current);
    if (index > 0) {
      return HERMES_STATES[index - 1];
    }
    return null;
  }

  /**
   * Check if state is a completed state in Hermes workflow
   */
  isHermesCompleted(state: HermesState): boolean {
    return ['done', 'testing', 'archiving'].includes(state);
  }

  /**
   * Check if state is an active state in Hermes workflow
   */
  isHermesActive(state: HermesState): boolean {
    return ['plan', 'propose', 'applying', 'code-review'].includes(state);
  }

  /**
   * Calculate progress percentage from task completion
   */
  calculateProgress(completedTasks: number, totalTasks: number): number {
    if (totalTasks === 0) return 0;
    return Math.round((completedTasks / totalTasks) * 100);
  }

  /**
   * Determine Hermes state based on progress
   */
  getStateFromProgress(progress: number, currentTaskState: string): HermesState {
    if (progress === 100) {
      return 'done';
    } else if (progress > 0) {
      return 'applying';
    } else if (currentTaskState === 'code-review') {
      return 'code-review';
    } else if (currentTaskState === 'testing') {
      return 'testing';
    } else {
      return 'propose';
    }
  }

  /**
   * Validate that a Redmine status name is known
   */
  isValidRedmineStatus(statusName: string): boolean {
    return Object.values(this.hermesMapping).includes(statusName) ||
           Object.values(this.bugMapping).includes(statusName) ||
           Object.values(this.customMapping).includes(statusName);
  }
}

/**
 * Create a default status mapper
 */
export function createDefaultMapper(): StatusMapper {
  return new StatusMapper();
}

/**
 * Create a status mapper from config
 */
export function createMapperFromConfig(config: ConfigurableStatusMappings): StatusMapper {
  return new StatusMapper(config);
}

/**
 * Get status transition label for display
 */
export function getStateTransitionLabel(from: string, to: string): string {
  return `${capitalize(from)} → ${capitalize(to)}`;
}

function capitalize(str: string): string {
  return str.replace(/-([a-z])/g, (_, char) => ` ${char.toUpperCase()}`).replace(/^./, c => c.toUpperCase());
}