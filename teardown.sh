set -x

MY_INSTANCE_NAME="sample-eta-server-instance"
ZONE=us-central1-a

gcloud compute instances delete $MY_INSTANCE_NAME \
   --zone=$ZONE --delete-disks=all

gcloud compute firewall-rules delete default-allow-http-8080
