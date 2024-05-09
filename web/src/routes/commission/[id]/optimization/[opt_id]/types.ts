import type {Readable} from "svelte/store";
import type {SolutionCommission} from "../optimization_types";

export type PossibleOptimizationStatuses = 'running' | 'ended' | 'not_started';

export type OptimizationStatus = Readable<{
    running: boolean;
    configurationLocked: boolean;
    solutions: { all: SolutionCommission[]; afternoon: SolutionCommission[]; morning: SolutionCommission[] };
    status: PossibleOptimizationStatuses
}>;