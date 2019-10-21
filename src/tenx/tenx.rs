// TenX utility functions as present in sourmash/sourmash/tenx.py
use rust_htslib::{bam, bam::Read};


pub fn read_barcodes_file(barcodes_file: &str) -> HashSet<String> {

    let barcode_fh = fs::read_to_string(barcodes_file);
    let barcodes: HashSet<std::string::String> = barcode_fh?.split_whitespace().map(|i| i.to_string()).collect();
    barcodes

}    


pub fn read_bam_file(bam_path: &str) -> bam.pileup.Alignment {

    
}
// alignment is a line in a bam file
pub fn pass_alignment_qc(alignment: bam.pileup.Alignment, barcodes: Vec<String>) {
    let bam  = bam::Reader::from_path(bam_file).unwrap();
    
    
}
