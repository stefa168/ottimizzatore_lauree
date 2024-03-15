export async function load({parent}) {
    const {commissionId, commissionData} = await parent();
    return {
        commissionId,
        commissionData
    };
}