#!/data2/external_data/Abyzov_Alexej_m124423/apps/plenv/versions/5.22.0/bin/perl
#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long;
use Pod::Usage;
use Bio::DB::Sam;

##----------------------
## Processing arguments
##----------------------

pod2usage(2) if @ARGV == 0;

my $ref_file;
my $clone_bam_file;
my $tissue_bam_file;
my $snp_list_file;

GetOptions ('ref|r=s'    => \$ref_file,
	    'clone|c=s'  => \$clone_bam_file,
	    'tissue|t:s' => \$tissue_bam_file,
	    'snp|s=s'    => \$snp_list_file
    ) or pod2usage(2);

##------
## Main
##------

if(defined $tissue_bam_file) {   
    print_header(1);
} else {
    print_header(0);
}

my $clone_sam  = Bio::DB::Sam->new(-fasta => $ref_file, -bam => $clone_bam_file);
my $tissue_sam = Bio::DB::Sam->new(-fasta => $ref_file, -bam => $tissue_bam_file) if defined $tissue_bam_file;
open (my $snp_list, "<", $snp_list_file);

while(<$snp_list>) {
    chomp $_;
    my ($chr, $pos, $ref, $alt) = split /\t/, $_;
    my $region = "$chr:$pos-$pos";

    print "$chr\t$pos\t$ref\t$alt";
    $clone_sam->pileup($region, process_pileup($pos, $ref, $alt));
    $tissue_sam->pileup($region, process_pileup($pos, $ref, $alt)) if defined $tissue_bam_file;
    print "\n";
}

close $snp_list;

##-----------------------------------------------------------

##---------------------------------
## Function definitions begin here
##---------------------------------

sub print_header {
    my $opt = shift; 
    if($opt == 0) {	
	print "#chr\tpos\tref\talt\tclone_f\tcl_total_reads\tcl_ref_count\tcl_alt_count\n";
    } elsif($opt == 1) {
	print "#chr\tpos\tref\talt\tclone_f\tcl_total_reads\tcl_ref_count\tcl_alt_count\ttissue_f\tti_total_reads\tti_ref_count\tti_alt_count\n";	
    }
}

sub process_pileup {
    my ($target_pos, $target_ref, $target_alt) = @_;
    $target_alt =~ s/,/|/g;

    return sub {
	my ($chr, $pos, $pileup) = @_;

	return unless $pos == $target_pos;

	my @pileup_seq =  map { substr($_->alignment->qseq, $_->qpos, 1) } @$pileup;

	my $total_reads = scalar @pileup_seq;
	my $ref_count = scalar grep(/$target_ref/, @pileup_seq);
	my $alt_count = scalar grep(/$target_alt/, @pileup_seq);

	my $alt_f = $alt_count / $total_reads;

	print "\t$alt_f\t$total_reads\t$ref_count\t$alt_count";
    };
}

##----------------------------------------------------------

##--------------
## Embedded POD
##--------------

__END__

=head1 NAME

get_AF.pl - getting allele frequencied from clone and tissue bam files

=head1 SYNOPSIS

get_AF.pl -r ref.fasta -c clone.bam [-t tissue.bam] -s snp.list

 Options:
   -r, --ref         reference genome fasta file
   -c, --clone       clone bam file
   -t, --tissue      tissue bam file
   -s, --snp         snp list file (format: chr\tpos\tref\talt)

=cut
